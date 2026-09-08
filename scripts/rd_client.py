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

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.raindrop.io/rest/v1"


class RaindropError(RuntimeError):
    pass


class RaindropClient:
    def __init__(self, token: str | None = None, min_interval: float = 0.35):
        self.token = token or os.environ.get("RD_API_TOKEN")
        if not self.token:
            raise RaindropError("RD_API_TOKEN not set")
        self.min_interval = min_interval  # conservative pacing between calls
        self._last_call = 0.0

    # -- low level ---------------------------------------------------------
    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        wait = self.min_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()
        req = urllib.request.Request(
            f"{API}{path}",
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code == 429:
                raise RaindropError(f"429 rate-limited on {method} {path}") from e
            raise RaindropError(f"HTTP {e.code} on {method} {path}: {body}") from e

    # -- reads -------------------------------------------------------------
    def user(self) -> dict:
        r = self._request("GET", "/user")
        if not r.get("result"):
            raise RaindropError("user() failed")
        return r["user"]

    def list_page(self, collection_id: int = 0, page: int = 0, perpage: int = 50) -> dict:
        return self._request(
            "GET", f"/raindrops/{collection_id}?perpage={perpage}&page={page}"
        )

    def list_all(self, collection_id: int = 0, perpage: int = 50) -> list[dict]:
        """All raindrops in a collection (0 = all), bulk fields included
        (title/link/domain/excerpt/type/tags/note)."""
        items: list[dict] = []
        page = 0
        while True:
            r = self.list_page(collection_id, page, perpage)
            batch = r.get("items", [])
            items.extend(batch)
            if len(batch) < perpage:
                return items
            page += 1

    def get(self, raindrop_id: int) -> dict | None:
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
        payload: dict = {}
        if note is not None:
            payload["note"] = note
        if tags is not None:
            payload["tags"] = tags
        if title is not None:
            payload["title"] = title
        r = self._request("PUT", f"/raindrop/{raindrop_id}", payload or {})
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
