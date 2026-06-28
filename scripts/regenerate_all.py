#!/usr/bin/env python3
"""
Regenerates HTML for ALL published town pages using the current template.
Run this once after any template/encoding changes to refresh all existing pages.
Does NOT call Groq (avoids rate limits) - uses fallback_copy for all pages.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from generate_page import (
    load_json, pick_service_subset, fallback_copy, render_html,
    regenerate_index, regenerate_sitemap,
    TOWNS_FILE, SERVICES_FILE, COORDS_FILE, LOCATIONS_DIR
)


def main():
    towns = load_json(TOWNS_FILE)
    services = load_json(SERVICES_FILE)
    coords = load_json(COORDS_FILE)

    published = [t for t in towns if t.get("published")]
    print(f"Re-rendering {len(published)} published town pages with fixed templates...")

    for town_entry in published:
        slug = town_entry["slug"]
        town = town_entry["town"]
        state = town_entry["state"]
        geo = coords.get(slug, {})
        county = geo.get("county", f"{state} service area")
        lat = geo.get("lat", "")
        lng = geo.get("lng", "")

        subset = pick_service_subset(slug, services)
        copy = fallback_copy(town, state, county, subset)
        html = render_html(town, state, county, lat, lng, slug, copy, subset)

        page_dir = LOCATIONS_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        with open(page_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  -> re-wrote locations/{slug}/index.html")

    regenerate_index(towns)
    regenerate_sitemap(towns)
    print(f"Done. {len(published)} pages re-rendered with encoding fix applied.")


if __name__ == "__main__":
    main()
