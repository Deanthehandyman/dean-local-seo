#!/usr/bin/env python3
"""
Pings IndexNow (covers Bing, and Bing-derived results) with newly published URLs
so they get crawled fast instead of waiting for a regular crawl cycle.

Run with: python3 scripts/ping_indexnow.py
"""

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOWNS_FILE = ROOT / "towns.json"
SITE_URL = os.environ.get("SITE_URL", "https://CHANGE-ME.netlify.app")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "0acf2d8096324058e815327524685b4c")


def main():
    with open(TOWNS_FILE) as f:
        towns = json.load(f)

    # Only ping for towns published in this run (simple approach: ping all published
    # towns each time; IndexNow does not penalize re-submission).
    published = [t for t in towns if t.get("published")]
    if not published:
        print("Nothing published yet, skipping IndexNow ping.")
        return

    url_list = [f"{SITE_URL}/locations/{t['slug']}/" for t in published]

    payload = {
        "host": SITE_URL.replace("https://", "").replace("http://", "").rstrip("/"),
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": url_list,
    }

    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"IndexNow ping sent. Status: {resp.status}")
    except Exception as e:
        print(f"WARNING: IndexNow ping failed: {e}")


if __name__ == "__main__":
    main()
