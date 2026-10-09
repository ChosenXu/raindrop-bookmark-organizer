#!/usr/bin/env python3
"""Selftests for scripts/rd_client.py (stdlib unittest, offline).

Run from the skill root:
    python3 -m unittest discover -s tests -v

The network layer is tested through a fake HTTPS connection injected via
RaindropClient._ensure_conn — no real token, no real network. Covers the
429 retry machinery (attempt counting, Retry-After, pacing adaptation,
probe-mode bypass), connection rebuild on stale/failed connections,
payload guards, update() readback comparison, and list_all() early stop.
"""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts")))

import rd_client as rdc  # noqa: E402


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status = status
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode()
        self._headers = headers or {}

    def read(self):
        return self._body

    def getheader(self, name):
        return self._headers.get(name)


class FakeConn:
    """Scripted connection: each getresponse() pops the next scripted item
    (a FakeResponse or an Exception)."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []
        self.closed = False

    def request(self, method, path, body=None, headers=None):
        self.requests.append((method, path))

    def getresponse(self):
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def close(self):
        self.closed = True


def make_client(script, token="test-token"):
    with mock.patch.dict(os.environ, {"RD_API_TOKEN": token}):
        rc = rdc.RaindropClient()
    conn = FakeConn(script)
    rc._conn = conn
    return rc, conn


class Retry429Tests(unittest.TestCase):
    def setUp(self):
        self.sleeps: list[float] = []
        p = mock.patch("time.sleep", self.sleeps.append)
        p.start()
        self.addCleanup(mock.patch.stopall)

    def test_429_then_success(self):
        rc, conn = make_client([
            FakeResponse(429, {}),
            FakeResponse(200, {"result": True, "item": {}}),
        ])
        out = rc._request("GET", "/raindrop/1")
        self.assertTrue(out["result"])
        self.assertEqual(len(conn.requests), 2)

    def test_429_respects_retry_after_header(self):
        rc, _ = make_client([
            FakeResponse(429, {}, headers={"Retry-After": "7"}),
            FakeResponse(200, {"result": True}),
        ])
        rc._request("GET", "/raindrop/1")
        self.assertIn(7.0, self.sleeps)

    def test_429_exhausts_attempts(self):
        rc, conn = make_client([FakeResponse(429, {})] * 4)
        with self.assertRaises(rdc.RaindropError) as cm:
            rc._request("GET", "/raindrop/1")
        self.assertIn("429", str(cm.exception))
        self.assertEqual(len(conn.requests), 4)

    def test_429_adapts_pacing(self):
        rc, _ = make_client([
            FakeResponse(429, {}),
            FakeResponse(200, {"result": True}),
        ])
        before = rc.min_interval
        rc._request("GET", "/raindrop/1")
        self.assertGreaterEqual(rc.min_interval, 0.5)
        self.assertGreater(rc.min_interval, before)
        self.assertLessEqual(rc.min_interval, 2.0)

    def test_probe_mode_surfaces_429_immediately(self):
        rc, conn = make_client([FakeResponse(429, {})])
        rc.retry_429 = False
        with self.assertRaises(rdc.RaindropError) as cm:
            rc._request("GET", "/raindrop/1")
        self.assertIn("429", str(cm.exception))
        self.assertEqual(len(conn.requests), 1)  # exactly one shot, no retry


class NetworkRetryTests(unittest.TestCase):
    def setUp(self):
        self.sleep = mock.patch("time.sleep", lambda s: None).start()
        self.addCleanup(mock.patch.stopall)

    def _client_with_conns(self, conns):
        with mock.patch.dict(os.environ, {"RD_API_TOKEN": "t"}):
            rc = rdc.RaindropClient()

        def ensure():
            conn = conns.pop(0)
            rc._conn = conn
            return conn

        rc._ensure_conn = mock.Mock(side_effect=ensure)
        return rc

    def test_stale_connection_rebuilt_and_retried(self):
        c1 = FakeConn([OSError("stale")])
        c2 = FakeConn([FakeResponse(200, {"result": True})])
        rc = self._client_with_conns([c1, c2])
        out = rc._request("GET", "/user")
        self.assertTrue(out["result"])
        self.assertTrue(rc._conn is c2)      # fresh conn in use
        self.assertTrue(c1.closed)           # broken conn was closed

    def test_network_error_exhausts_attempts(self):
        conns = [FakeConn([OSError("down")]) for _ in range(4)]
        rc = self._client_with_conns(conns)
        with self.assertRaises(rdc.RaindropError) as cm:
            rc._request("GET", "/user")
        self.assertIn("network error", str(cm.exception))

    def test_http_error_status_raises(self):
        rc, _ = make_client([FakeResponse(500, {"error": "boom"})])
        with self.assertRaises(rdc.RaindropError) as cm:
            rc._request("GET", "/user")
        self.assertIn("500", str(cm.exception))


class GuardTests(unittest.TestCase):
    def test_missing_token_raises(self):
        env = {k: v for k, v in os.environ.items() if k != "RD_API_TOKEN"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(rdc.RaindropError):
                rdc.RaindropClient()

    def test_non_int_id_rejected_before_url(self):
        rc, conn = make_client([])
        for bad in ("123/..", None, 1.5):
            with self.assertRaises(rdc.RaindropError):
                rc.get(bad)
        self.assertEqual(conn.requests, [])  # nothing ever hit the wire

    def test_update_empty_payload_refused(self):
        rc, conn = make_client([])
        with self.assertRaises(rdc.RaindropError) as cm:
            rc.update(1)
        self.assertIn("refused", str(cm.exception))
        self.assertEqual(conn.requests, [])

    def test_list_page_non_int_collection_rejected(self):
        rc, _ = make_client([])
        with self.assertRaises(rdc.RaindropError):
            rc.list_page("0")


class UpdateReadbackTests(unittest.TestCase):
    def test_matching_readback_applied(self):
        rc, conn = make_client([
            FakeResponse(200, {"result": True}),            # PUT
            FakeResponse(200, {"result": True,
                               "item": {"note": "n", "tags": ["b", "a"]}}),  # GET readback
        ])
        res = rc.update(1, note="n", tags=["a", "b"])
        self.assertTrue(res["applied"])
        self.assertEqual(conn.requests[0][0], "PUT")

    def test_mismatched_tags_not_applied(self):
        rc, _ = make_client([
            FakeResponse(200, {"result": True}),
            FakeResponse(200, {"result": True,
                               "item": {"note": "n", "tags": ["x"]}}),
        ])
        res = rc.update(1, note="n", tags=["a"])
        self.assertFalse(res["applied"])

    def test_put_result_false_not_applied(self):
        rc, _ = make_client([FakeResponse(200, {"result": False})])
        res = rc.update(1, note="n")
        self.assertFalse(res["applied"])


class ListAllTests(unittest.TestCase):
    def test_stops_when_count_reached(self):
        page = {"result": True, "count": 2,
                "items": [{"_id": 1}, {"_id": 2}]}
        rc, conn = make_client([FakeResponse(200, page)])
        items = rc.list_all(0, perpage=2)
        self.assertEqual(len(items), 2)
        self.assertEqual(len(conn.requests), 1)  # early stop: no extra page

    def test_paginates_short_pages(self):
        p0 = {"result": True, "count": 3, "items": [{"_id": 1}]}
        p1 = {"result": True, "count": 3, "items": [{"_id": 2}, {"_id": 3}]}
        rc, conn = make_client([FakeResponse(200, p0), FakeResponse(200, p1)])
        items = rc.list_all(0, perpage=1)
        self.assertEqual([i["_id"] for i in items], [1, 2, 3])
        self.assertEqual(len(conn.requests), 2)


if __name__ == "__main__":
    unittest.main()
