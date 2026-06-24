#!/usr/bin/env python3
"""
Local SEO page generator for Dean's Handyman Service LLC.

Each run:
1. Picks the next unpublished town from towns.json (deterministic order, top to bottom).
2. Selects a rotating subset of 9 real services from services.json (grounded against
   the live Square catalog, so no hallucinated pricing or services).
3. Calls Groq to write unique, non-templated page copy.
4. Renders a static HTML page into locations/<slug>/index.html.
5. Marks the town as published in towns.json.
6. Regenerates sitemap.xml and index.html (the directory of all published pages).

Run with: python3 scripts/generate_page.py
Env var required: GROQ_API_KEY
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
TOWNS_FILE = ROOT / "towns.json"
SERVICES_FILE = ROOT / "services.json"
LOCATIONS_DIR = ROOT / "locations"
SITE_URL = os.environ.get("SITE_URL", "https://CHANGE-ME.netlify.app")
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "2"))
BOOKING_URL = "https://deanshandymanservice.square.site"

PHONE = "281-917-9914"
BUSINESS_NAME = "Dean's Handyman Service LLC"
BASE_CITY = "Pittsburg, TX"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def pick_service_subset(town_slug, services, count=9):
    """Deterministic rotation so every town doesn't show the identical 9 services."""
    h = int(hashlib.sha256(town_slug.encode()).hexdigest(), 16)
    n = len(services)
    start = h % n
    rotated = services[start:] + services[:start]
    return rotated[:count]


def call_groq(town, state, services_subset):
    """Call Groq for grounded, unique page copy. Falls back to a template if the
    API key is missing or the call fails, so a bad run never blocks the pipeline."""
    api_key = os.environ.get("GROQ_API_KEY")
    service_list_str = "\n".join(
        f"- {s['name']} ({', '.join(s['categories'])}): {s['short_description']}"
        for s in services_subset
    )

    prompt = f"""You are writing a local service-area landing page for {BUSINESS_NAME}, a real handyman/technical installation business based in {BASE_CITY}. The business is run by Dean, a certified Starlink installer who specializes in Starlink installation, smart home tech, networking, electrical work, and RV tech support.

Write landing page copy for the town of {town}, {state}. Use ONLY the real services listed below — do not invent services, prices, or guarantees not implied by the descriptions.

REAL SERVICES OFFERED (use these, in your own words, do not copy verbatim):
{service_list_str}

Write:
1. A page title (under 60 characters, must include "{town}" and a core service like Starlink or handyman)
2. A meta description (under 155 characters)
3. An H1 headline (different phrasing than the title)
4. A 2-3 sentence intro paragraph mentioning {town} by name and the surrounding area
5. A 1-sentence transition into the services list

Respond ONLY with valid JSON in this exact shape, no markdown fences, no commentary:
{{"title": "...", "meta_description": "...", "h1": "...", "intro": "...", "services_intro": "..."}}
"""

    if not api_key:
        print("WARNING: GROQ_API_KEY not set, using fallback template copy.")
        return fallback_copy(town, state)

    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 600,
            }).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(content)
    except Exception as e:
        print(f"WARNING: Groq call failed ({e}), using fallback template copy.")
        return fallback_copy(town, state)


def fallback_copy(town, state):
    return {
        "title": f"Starlink & Handyman Services in {town}, {state}",
        "meta_description": f"Certified Starlink installation, smart home setup, networking, and electrical services in {town}, {state}. Call or text {PHONE}.",
        "h1": f"Starlink Installation & Technical Services Serving {town}, {state}",
        "intro": f"{BUSINESS_NAME} proudly serves {town}, {state} and the surrounding area with certified Starlink installation, smart home setup, networking, and electrical work. Based in {BASE_CITY}, Dean brings honest, technical expertise to every job.",
        "services_intro": f"Here's what {BUSINESS_NAME} offers homeowners and businesses in {town}:",
    }


def render_html(town, state, slug, copy, services_subset):
    service_items = "\n".join(
        f"""        <div class="service-card">
          <h3>{s['name']}</h3>
          <p>{s['short_description']}</p>
        </div>"""
        for s in services_subset
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{copy['title']}</title>
<meta name="description" content="{copy['meta_description']}">
<link rel="canonical" href="{SITE_URL}/locations/{slug}/">
<meta property="og:title" content="{copy['title']}">
<meta property="og:description" content="{copy['meta_description']}">
<meta property="og:type" content="website">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{BUSINESS_NAME}",
  "telephone": "{PHONE}",
  "areaServed": {{"@type": "City", "name": "{town}, {state}"}},
  "address": {{"@type": "PostalAddress", "addressLocality": "Pittsburg", "addressRegion": "TX"}}
}}
</script>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; background: #1a1d1f; color: #e8e8e8; }}
  header {{ background: #2b2f31; padding: 2rem 1.5rem; border-bottom: 3px solid #c9472b; }}
  header h1 {{ margin: 0 0 0.5rem; font-size: 1.8rem; color: #ffffff; }}
  .intro {{ max-width: 760px; margin: 1.5rem auto; padding: 0 1.5rem; line-height: 1.6; }}
  .services {{ max-width: 900px; margin: 0 auto 2rem; padding: 0 1.5rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }}
  .service-card {{ background: #24272a; border-left: 4px solid #3a6f7a; padding: 1rem 1.2rem; border-radius: 4px; }}
  .service-card h3 {{ margin: 0 0 0.4rem; font-size: 1.05rem; color: #f0f0f0; }}
  .service-card p {{ margin: 0; font-size: 0.92rem; color: #b8b8b8; line-height: 1.5; }}
  .cta {{ text-align: center; padding: 2rem 1.5rem; }}
  .cta a {{ display: inline-block; background: #c9472b; color: white; padding: 0.9rem 1.8rem; border-radius: 4px; text-decoration: none; font-weight: bold; }}
  footer {{ text-align: center; padding: 1.5rem; font-size: 0.85rem; color: #777; }}
</style>
</head>
<body>
<header>
  <h1>{copy['h1']}</h1>
</header>
<div class="intro">
  <p>{copy['intro']}</p>
  <p>{copy['services_intro']}</p>
</div>
<div class="services">
{service_items}
</div>
<div class="cta">
  <a href="{BOOKING_URL}">Book a Service Call \u2014 {PHONE}</a>
</div>
<footer>
  {BUSINESS_NAME} &middot; Serving {town}, {state} and the surrounding 200-mile area
</footer>
</body>
</html>
"""


def regenerate_sitemap(towns):
    published = [t for t in towns if t.get("published")]
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/locations/{t['slug']}/" for t in published]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{now}</lastmod></url>" for u in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'
    with open(ROOT / "sitemap.xml", "w") as f:
        f.write(xml)


def regenerate_index(towns):
    published = [t for t in towns if t.get("published")]
    items = "\n".join(
        f'      <li><a href="/locations/{t["slug"]}/">{t["town"]}, {t["state"]}</a></li>'
        for t in published
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Service Areas \u2014 {BUSINESS_NAME}</title>
<meta name="description" content="Starlink installation, smart home, networking, and RV tech services across East Texas, Southwest Arkansas, Northwest Louisiana, and Southeast Oklahoma.">
<style>body{{font-family:Arial,sans-serif;background:#1a1d1f;color:#e8e8e8;max-width:700px;margin:2rem auto;padding:0 1.5rem;}}
a{{color:#7fc8d6;}}h1{{color:#fff;}}ul{{line-height:1.9;}}</style>
</head>
<body>
<h1>{BUSINESS_NAME} \u2014 Service Areas</h1>
<p>{len(published)} of 45 service-area pages published so far.</p>
<ul>
{items}
</ul>
</body>
</html>
"""
    with open(ROOT / "index.html", "w") as f:
        f.write(html)


def main():
    towns = load_json(TOWNS_FILE)
    services = load_json(SERVICES_FILE)

    pending = [t for t in towns if not t.get("published")]
    if not pending:
        print("All towns published. Nothing to do.")
        return

    batch = pending[:PAGES_PER_RUN]
    for town_entry in batch:
        slug = town_entry["slug"]
        town = town_entry["town"]
        state = town_entry["state"]
        print(f"Generating page for {town}, {state} ({slug})...")

        subset = pick_service_subset(slug, services)
        copy = call_groq(town, state, subset)
        html = render_html(town, state, slug, copy, subset)

        page_dir = LOCATIONS_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        with open(page_dir / "index.html", "w") as f:
            f.write(html)

        town_entry["published"] = True
        town_entry["published_at"] = datetime.now(timezone.utc).isoformat()
        print(f"  -> wrote locations/{slug}/index.html")

    save_json(TOWNS_FILE, towns)
    regenerate_sitemap(towns)
    regenerate_index(towns)
    print(f"Done. {len(batch)} page(s) generated this run.")


if __name__ == "__main__":
    main()
