"""
build_data.py — DM Vault data builder
Fetches all standard content from the open5e API and writes compact JSON
files to static/data/ for GitHub Pages hosting.

Run from the dm_site folder:
    python scripts/build_data.py

Also copies your campaign content (NPCs, locations) from cache/ to static/data/.
"""

import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

OPEN5E = "https://api.open5e.com/v1"
OUT    = Path(__file__).parent.parent / "data"
CACHE  = Path(__file__).parent.parent.parent / "cache"

# How many items to fetch per page
PAGE_SIZE = 5000

# ── open5e endpoints → output filename ────────────────────────────
ENDPOINTS = {
    "monsters":    "monsters",
    "spells":      "spells",
    "magicitems":  "magic_items",
    "weapons":     "items",
    "races":       "races",
    "classes":     "classes",
    "backgrounds": "backgrounds",
    "feats":       "feats",
}

def fetch_all(endpoint: str) -> list:
    results = []
    url = f"{OPEN5E}/{endpoint}/?limit={PAGE_SIZE}&format=json"
    while url:
        print(f"  fetching {url[:80]}...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"ERROR: {e}")
            break
        page = data.get("results", data) if isinstance(data, dict) else data
        results.extend(page)
        url = data.get("next") if isinstance(data, dict) else None
        print(f"{len(page)} items")
        if url:
            time.sleep(0.25)   # be polite to the API
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {OUT}\n")

    # ── open5e sections ────────────────────────────────────────────
    for endpoint, filename in ENDPOINTS.items():
        print(f"[{filename}] Fetching from open5e/{endpoint}...")
        items = fetch_all(endpoint)
        if not items:
            print(f"  WARNING: no data returned for {endpoint}")
            continue
        out_path = OUT / f"{filename}.json"
        out_path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        print(f"  → {out_path.name}: {len(items)} items ({out_path.stat().st_size // 1024} KB)\n")

    # ── campaign content from cache ────────────────────────────────
    print("[campaign] Copying NPCs and locations from cache...")
    for name in ("npcs", "locations"):
        src = CACHE / f"{name}.json"
        dst = OUT / f"{name}.json"
        if src.exists():
            shutil.copy2(src, dst)
            data = json.loads(dst.read_text(encoding="utf-8"))
            print(f"  → {name}.json: {len(data)} entries")
        else:
            print(f"  WARNING: cache/{name}.json not found — skipping")

    print("\nDone! Commit static/data/ to GitHub to publish the data.")


if __name__ == "__main__":
    main()
