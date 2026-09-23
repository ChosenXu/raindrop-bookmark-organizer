#!/usr/bin/env python3
"""rd_client.py — Raindrop.io REST v1 client for raindrop-bookmark-organizer.

Credentials: reads RD_API_TOKEN from the environment. Never hardcode.

Usage:
  from rd_client import RaindropClient
  rc = RaindropClient()
  for item in rc.list_all(0):          # 0 = all collections
      ...

Smoke test (creates and cleans up its own data):
  RD_API_TOKEN=... python3 rd_client.py --smoke

Rate-limit probe:
  RD_API_TOKEN=... python3 rd_client.py --rate-probe [N]
"""

from __future__ import annotations

import http.client
import json
import os
import sys
import time

API = "https://api.raindrop.io/rest/v1"
HOST = "api.raindrop.io"


class RaindropError(RuntimeError):
    pass


class RaindropClient:
    def __init__(self, token: str | None = None, min_interval: float = 0.35):
        self.token = token or os.environ.get("RD_API_TOKEN")
        if not self.token:
            raise RaindropError("RD_API_TOKEN not set")
        self.min_interval = min_interval  # pacing between calls; adapts up on 429
        self._last_call = 0.0
        self._conn: http.client.HTTPSConnection | None = None

    # -- low level ---------------------------------------------------------
    def _ensure_conn(self) -> http.client.HTTPSConnection:
        """One persistent connection per client (TCP+TLS handshake reused)."""
        if self._conn is None:
            self._conn = http.client.HTTPSConnection(HOST, timeout=30)
        return self._conn

    def _close_conn(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None

    def close(self) -> None:
        self._close_conn()

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        attempts = 4
        for attempt in range(1, attempts + 1):
            wait = self.min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                conn = self._ensure_conn()
                conn.request(method, path, body=body, headers=headers)
                resp = conn.getresponse()
                data = resp.read().decode(errors="replace")
                if resp.status == 429:
                    retry_after = resp.getheader("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 3 * attempt
                    except ValueError:  # non-numeric Retry-After (HTTP-date etc.)
                        delay = 3 * attempt
                    if attempt == attempts:
                        raise RaindropError(
                            f"429 rate-limited on {method} {path} after {attempts} attempts")
                    # adapt pacing so subsequent calls slow down
                    # (floor 0.5s: even an unpaced probe backs off after a 429)
                    self.min_interval = min(max(self.min_interval * 1.5, 0.5), 2.0)
                    print(f"  [429] {method} {path} — retrying in {delay:.0f}s "
                          f"(pacing now {self.min_interval:.2f}s)", flush=True)
                    time.sleep(delay)
                    continue
                if not 200 <= resp.status < 300:
                    raise RaindropError(
                        f"HTTP {resp.status} on {method} {path}: {data[:300]}")
                return json.loads(data)
            except RaindropError:
                raise
            except (http.client.HTTPException, OSError, json.JSONDecodeError) as e:
                # stale/broken connection or transient network failure:
                # rebuild the connection and retry with backoff
                self._close_conn()
                if attempt == attempts:
                    raise RaindropError(
                        f"network error on {method} {path} after {attempts} attempts: {e}") from e
                backoff = 3 * attempt
                print(f"  [retry {attempt}/{attempts-1}] {method} {path}: {e} "
                      f"— backing off {backoff}s", flush=True)
                time.sleep(backoff)
        raise RaindropError(f"request failed on {method} {path}")  # unreachable

    # -- reads -------------------------------------------------------------
    def user(self) -> dict:
        r = self._request("GET", "/user")
        if not r.get("result"):
            raise RaindropError("user() failed")
        return r["user"]

    def list_page(self, collection_id: int = 0, page: int = 0, perpage: int = 50) -> dict:
        if not isinstance(collection_id, int):
            raise RaindropError(f"invalid collection id: {collection_id!r}")
        return self._request(
            "GET", f"/raindrops/{collection_id}?perpage={perpage}&page={page}"
        )

    def list_all(self, collection_id: int = 0, perpage: int = 50) -> list[dict]:
        """All raindrops in a collection (0 = all), bulk fields included
        (title/link/domain/excerpt/type/tags/note). Stops early once the
        reported total count is reached (avoids one extra empty page when
        the library size is an exact multiple of perpage)."""
        items: list[dict] = []
        page = 0
        while True:
            r = self.list_page(collection_id, page, perpage)
            batch = r.get("items", [])
            items.extend(batch)
            count = r.get("count")
            if len(batch) < perpage:
                return items
            if isinstance(count, int) and len(items) >= count:
                return items
            page += 1

    def get(self, raindrop_id: int) -> dict | None:
        if not isinstance(raindrop_id, int):
            raise RaindropError(f"invalid raindrop id: {raindrop_id!r}")
        r = self._request("GET", f"/raindrop/{raindrop_id}")
        return r.get("item") if r.get("result") else None

    # -- writes (with verification readback) --------------------------------
    def update(
        self,
        raindrop_id: int,
        note: str | None = None,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> dict:
        """Single-field-group update. Returns {'applied': bool, 'item': readback}."""
        if not isinstance(raindrop_id, int):
            raise RaindropError(f"invalid raindrop id: {raindrop_id!r}")
        payload: dict = {}
        if note is not None:
            payload["note"] = note
        if tags is not None:
            payload["tags"] = tags
        if title is not None:
            payload["title"] = title
        if not payload:
            raise RaindropError(
                "update() refused: note/tags/title are all None (nothing to write)")
        r = self._request("PUT", f"/raindrop/{raindrop_id}", payload)
        if not r.get("result"):
            return {"applied": False, "item": None}
        item = self.get(raindrop_id)
        ok = True
        if note is not None and (item or {}).get("note") != note:
            ok = False
        if tags is not None and sorted((item or {}).get("tags") or []) != sorted(tags):
            ok = False
        if title is not None and (item or {}).get("title") != title:
            ok = False
        return {"applied": ok, "item": item}

    # -- collections --------------------------------------------------------
    def create_collection(self, title: str) -> int | None:
        r = self._request("POST", "/collection", {"title": title})
        return (r.get("item") or {}).get("_id")

    def delete_collection(self, collection_id: int) -> bool:
        if not isinstance(collection_id, int):
            raise RaindropError(f"invalid collection id: {collection_id!r}")
        r = self._request("DELETE", f"/collection/{collection_id}")
        return bool(r.get("result"))


def _smoke() -> int:
    """create -> update(note+tags) -> verify -> delete, on a scratch collection."""
    rc = RaindropClient()
    u = rc.user()
    print(f"user: {u['_id']} ({u.get('fullName')})")
    cid = rc.create_collection("rd-client-smoke")
    assert cid, "collection create failed"
    print(f"scratch collection: {cid}")
    try:
        r = rc._request(
            "POST",
            "/raindrop",
            {"link": "https://example.com/rd-client-smoke", "title": "smoke",
             "collection": {"$id": cid}, "tags": ["smoke-a"]},
        )
        rid = r["item"]["_id"]
        print(f"seed raindrop: {rid}, tags={r['item'].get('tags')}")
        res = rc.update(rid, note="test note", tags=["smoke-b", "smoke-c"])
        print(f"update verified: {res['applied']}, tags now: {res['item']['tags']}")
        res2 = rc.update(rid, tags=["smoke-b"])  # replace semantics check
        print(f"replace to [smoke-b]: applied={res2['applied']}, tags={res2['item']['tags']}")
        return 0 if res["applied"] and res2["applied"] else 1
    finally:
        # cleanup: delete raindrop then collection
        rid_local = None
        try:
            items = rc.list_all(cid)
            for it in items:
                rc._request("DELETE", f"/raindrop/{it['_id']}")
                rid_local = it["_id"]
            print(f"cleaned raindrops in {cid}")
        except Exception as e:  # noqa: BLE001
            print(f"cleanup warning: {e}")
        rc.delete_collection(cid)
        print("scratch collection deleted")


def _rate_probe(n: int = 40) -> int:
    rc = RaindropClient(min_interval=0.0)  # no pacing: find the real limit
    codes = {"ok": 0, "429": 0, "err": 0}
    t0 = time.monotonic()
    for i in range(n):
        try:
            rc.list_page(0, perpage=1)
            codes["ok"] += 1
        except RaindropError as e:
            if "429" in str(e):
                codes["429"] += 1
                time.sleep(1.0)
            else:
                codes["err"] += 1
                print("err:", e)
    dt = time.monotonic() - t0
    print(f"{n} rapid GETs in {dt:.1f}s -> ok={codes['ok']} 429={codes['429']} err={codes['err']}")
    return codes["429"]


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        sys.exit(_smoke())
    elif "--rate-probe" in sys.argv:
        i = sys.argv.index("--rate-probe")
        n = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 40
        sys.exit(1 if _rate_probe(n) else 0)
    else:
        print(__doc__)
