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
COORDS_FILE = ROOT / "coordinates.json"
LOCATIONS_DIR = ROOT / "locations"
SITE_URL = os.environ.get("SITE_URL", "https://deanthehandyman.github.io/dean-local-seo")
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "2"))
BOOKING_URL = "https://deanshandymanservice.square.site"
DIRECT_BOOKING_URL = "https://book.squareup.com/appointments/6adhz55czkh9i7/location/LRQVC65X9CQJK/services?buttonTextColor=ffffff&color=0019ff&locale=en&referrer=so&team_member_id=TM41qxXARrQWpS86"

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


def call_groq(town, state, county, services_subset):
    """Call Groq for grounded, unique page copy. Falls back to a template if the
    API key is missing or the call fails, so a bad run never blocks the pipeline."""
    api_key = os.environ.get("GROQ_API_KEY")
    service_list_str = "\n".join(
        f"- {s['name']} ({', '.join(s['categories'])}): {s['short_description']}"
        for s in services_subset
    )
    service_names_str = ", ".join(s['name'] for s in services_subset)

    prompt = f"""You are writing a local service-area landing page for {BUSINESS_NAME}, a real handyman/technical installation business based in {BASE_CITY}. The business is run by Dean, a certified Starlink installer who specializes in Starlink installation, smart home tech, networking, electrical work, and RV tech support.

Write landing page copy for the town of {town}, {state} (located in {county}). Use ONLY the real services listed below — do not invent services, prices, or guarantees not implied by the descriptions.

REAL SERVICES OFFERED (use these, in your own words, do not copy verbatim):
{service_list_str}

Write the following, each genuinely unique to {town} (not generic boilerplate that could apply to any town):

1. A page title (under 60 characters, must include "{town}" and a core service like Starlink or handyman)
2. A meta description (under 155 characters)
3. An H1 headline (different phrasing than the title)
4. A 2-3 sentence intro paragraph that opens by naming the real problem residents of {town} face — slow, capped, or unreliable internet from rural providers like Viasat, HughesNet, or fixed wireless — before introducing Starlink as the fix. Mention {town} and {county} by name. Do not assume the reader already knows what Starlink is or how it differs from satellite internet they may have tried before (briefly imply it's not the same as old satellite internet — no harsh data caps, much faster speeds).
5. A section header introducing the services list (vary this — do NOT always write "Our Services" or "Premium Services", make it specific to {town} or the service mix, e.g. "How We Help {town} Homeowners Stay Connected")
6. A 1-sentence transition into the services list
7. Exactly 4 FAQ question-and-answer pairs that a real local customer in {town} would search for or ask an AI assistant, naturally incorporating {town} and/or {county} into at least one question or answer. Base answers only on the real services listed above — do not invent guarantees, pricing, or turnaround times not implied by the service descriptions. Questions should sound like real voice-search or AI-assistant queries, not generic FAQ boilerplate. At least one of the 4 FAQs MUST directly compare Starlink to Viasat and/or HughesNet (e.g. a question like "Is Starlink better than Viasat in {county}?" or "Why switch from HughesNet to Starlink in {town}?"), with an answer that names the specific advantage (no hard data caps, lower latency for video calls/streaming/gaming, faster installation) without disparaging the competitor by name beyond factual comparison.

Respond ONLY with valid JSON in this exact shape, no markdown fences, no commentary:
{{"title": "...", "meta_description": "...", "h1": "...", "intro": "...", "services_header": "...", "services_intro": "...", "faqs": [{{"q": "...", "a": "..."}}, {{"q": "...", "a": "..."}}, {{"q": "...", "a": "..."}}]}}
"""

    if not api_key:
        print("WARNING: GROQ_API_KEY not set, using fallback template copy.")
        return fallback_copy(town, state, county, services_subset)

    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1100,
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
            parsed = json.loads(content)
            if "faqs" not in parsed or len(parsed.get("faqs", [])) < 1:
                raise ValueError("Groq response missing FAQs")
            return parsed
    except Exception as e:
        print(f"WARNING: Groq call failed ({e}), using fallback template copy.")
        return fallback_copy(town, state, county, services_subset)


def fallback_copy(town, state, county, services_subset):
    top_service = services_subset[0]["name"] if services_subset else "Starlink installation"
    second_service = services_subset[1]["name"] if len(services_subset) > 1 else "smart home setup"
    return {
        "title": f"Starlink Installation in {town}, {state} | Ditch Viasat & HughesNet",
        "meta_description": f"Tired of slow Viasat or HughesNet in {town}, {state}? Certified Starlink installation, smart home setup, networking, and electrical services in {county}. Call {PHONE}.",
        "h1": f"Starlink Installation Serving {town}, {state} — A Real Upgrade From Viasat & HughesNet",
        "intro": f"If you're stuck with slow speeds, data caps, or high latency from Viasat or HughesNet in {town}, {state}, you have a better option. {BUSINESS_NAME} provides certified Starlink installation throughout {town} and all of {county}, plus smart home setup, networking, and electrical work. Based in {BASE_CITY}, Dean brings honest, technical expertise to every job.",
        "services_header": f"How {BUSINESS_NAME} Helps {town} Stay Connected",
        "services_intro": f"Here's what {BUSINESS_NAME} offers homeowners and businesses in {town}:",
        "faqs": [
            {
                "q": f"Does anyone install Starlink near {town}, {state}?",
                "a": f"Yes — {BUSINESS_NAME} provides certified Starlink installation throughout {town} and the rest of {county}, including dish mounting, cable routing, and Wi-Fi optimization.",
            },
            {
                "q": f"Is Starlink better than Viasat or HughesNet in {county}?",
                "a": f"For most homes in {county}, yes. Starlink doesn't carry the hard data caps that Viasat and HughesNet plans typically impose, and latency is low enough for video calls, streaming, and gaming — something traditional geostationary satellite internet struggles with.",
            },
            {
                "q": f"Who offers {top_service} in {county}?",
                "a": f"{BUSINESS_NAME} offers {top_service} as part of its mobile service across {county} and the surrounding 200-mile area, based out of {BASE_CITY}.",
            },
            {
                "q": f"Can I get {second_service} done in {town}?",
                "a": f"Yes, {second_service} is one of the core services {BUSINESS_NAME} provides to customers in {town} and nearby communities in {county}.",
            },
        ],
    }


def render_html(town, state, county, lat, lng, slug, copy, services_subset):
    service_items = "\n".join(
        f"""        <div class="service-block">
          <h3>{s['name']}</h3>
          <p>{s['short_description']}</p>
        </div>"""
        for s in services_subset
    )

    faqs = copy.get("faqs", [])
    faq_items_html = "\n".join(
        f"""        <div class="faq-item">
          <h3>{f['q']}</h3>
          <p>{f['a']}</p>
        </div>"""
        for f in faqs
    )

    # FAQPage schema -- this is the block AI answer engines and Google's AI
    # Overviews extract directly for "near me" / voice-search style queries.
    faq_schema_entities = ",\n".join(
        f"""    {{
      "@type": "Question",
      "name": {json.dumps(f['q'])},
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": {json.dumps(f['a'])}
      }}
    }}"""
        for f in faqs
    )

    # Service schema per offering -- machine-readable list of what's offered
    # in this specific town, distinct from the plain-HTML version below.
    service_schema_entities = ",\n".join(
        f"""    {{
      "@type": "Service",
      "name": {json.dumps(s['name'])},
      "description": {json.dumps(s['short_description'])},
      "areaServed": {{"@type": "City", "name": {json.dumps(town + ', ' + state)}}},
      "provider": {{"@type": "LocalBusiness", "name": {json.dumps(BUSINESS_NAME)}}}
    }}"""
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
<meta name="theme-color" content="#0019ff">
<meta name="geo.placename" content="{town}, {state}">
<meta name="geo.position" content="{lat};{lng}">
<meta name="ICBM" content="{lat}, {lng}">
<meta name="google-site-verification" content="Ppwb67jnNZqenhH9knICRsS0JoWsvO_G5isyaixaDwk" />
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{BUSINESS_NAME}",
  "telephone": "{PHONE}",
  "address": {{
    "@type": "PostalAddress",
    "addressLocality": "Pittsburg",
    "addressRegion": "TX",
    "addressCountry": "US"
  }},
  "geo": {{
    "@type": "GeoCoordinates",
    "latitude": {lat},
    "longitude": {lng}
  }},
  "areaServed": {{
    "@type": "City",
    "name": "{town}, {state}",
    "containedInPlace": {{
      "@type": "AdministrativeArea",
      "name": "{county}"
    }}
  }},
  "priceRange": "$$"
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{faq_schema_entities}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
{service_schema_entities}
  ]
}}
</script>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    margin: 0;
    background: #ffffff;
    color: #1a1a1a;
    line-height: 1.6;
  }}
  .topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    background: #ffffff;
    max-width: 900px;
    margin: 0 auto;
  }}
  .topbar .brand {{ font-weight: 700; font-size: 1.05rem; color: #1a1a1a; }}
  .topbar .call-btn {{
    background: #0019ff;
    color: #fff;
    border-radius: 999px;
    padding: 0.55rem 1.3rem;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none;
  }}
  .hero {{
    background: linear-gradient(rgba(10,10,20,0.55), rgba(10,10,20,0.65)),
                url('https://square.online/uploads/b/d33d364aeda28955d9a1ba370fc021a9d9a8538ef34f7f453fc9759a34697f4c/20250730_170809_1781297295.jpg');
    background-size: cover;
    background-position: center;
    color: #fff;
    padding: 3rem 1.5rem 3.5rem;
    text-align: center;
  }}
  .hero-inner {{
    max-width: 640px;
    margin: 0 auto;
    text-align: left;
  }}
  .hero .eyebrow {{
    display: inline-block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: #fff;
  }}
  .hero h1 {{
    font-size: 2.1rem;
    font-weight: 800;
    margin: 0 0 1rem;
    line-height: 1.15;
  }}
  .hero p {{
    font-size: 1rem;
    max-width: 640px;
    margin: 0 0 1.5rem;
    color: #f0f0f0;
  }}
  .btn-primary {{
    display: block;
    width: 100%;
    max-width: 420px;
    text-align: center;
    background: #0019ff;
    color: #fff;
    padding: 0.95rem 1.5rem;
    border-radius: 999px;
    font-weight: 700;
    text-decoration: none;
    margin: 0 auto 0.85rem;
    font-size: 1.02rem;
  }}
  .btn-secondary {{
    display: block;
    width: 100%;
    max-width: 420px;
    text-align: center;
    background: #ffffff;
    color: #0019ff;
    border: 2px solid #0019ff;
    padding: 0.9rem 1.5rem;
    border-radius: 999px;
    font-weight: 700;
    text-decoration: none;
    margin: 0 auto;
    font-size: 1.02rem;
  }}
  .intro-section {{
    max-width: 760px;
    margin: 0 auto;
    padding: 2.25rem 1.5rem;
    text-align: center;
  }}
  .intro-section p {{
    font-size: 1rem;
    color: #333;
  }}
  .intro-section strong {{ color: #0019ff; }}
  .services-section {{
    background: #f4f5f7;
    padding: 2.5rem 1.5rem;
  }}
  .services-section h2 {{
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0 0 1.75rem;
    color: #111;
  }}
  .services-wrap {{
    max-width: 720px;
    margin: 0 auto;
  }}
  .service-block {{
    margin-bottom: 1.5rem;
    text-align: center;
  }}
  .service-block h3 {{
    color: #0019ff;
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0 0 0.35rem;
  }}
  .service-block p {{
    margin: 0;
    color: #444;
    font-size: 0.95rem;
  }}
  .faq-section {{
    max-width: 720px;
    margin: 0 auto;
    padding: 2.5rem 1.5rem;
  }}
  .faq-section h2 {{
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0 0 1.75rem;
    color: #111;
  }}
  .faq-item {{
    margin-bottom: 1.5rem;
    text-align: center;
  }}
  .faq-item h3 {{
    font-size: 1.02rem;
    font-weight: 700;
    color: #111;
    margin: 0 0 0.35rem;
  }}
  .faq-item p {{
    margin: 0;
    color: #444;
    font-size: 0.95rem;
  }}
  .cta-section {{
    text-align: center;
    padding: 2.5rem 1.5rem;
  }}
  .cta-section h2 {{
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0 0 1.25rem;
    color: #111;
  }}
  footer {{
    text-align: center;
    padding: 2rem 1.5rem;
    font-size: 0.85rem;
    color: #777;
    background: #fafafa;
    border-top: 1px solid #eee;
  }}
  footer .phone {{ color: #0019ff; font-weight: 600; text-decoration: none; }}
</style>
</head>
<body>
<div class="topbar">
  <span class="brand">{BUSINESS_NAME}</span>
  <a class="call-btn" href="tel:{PHONE}">Call Now</a>
</div>

<div class="hero">
  <div class="hero-inner">
    <span class="eyebrow">\u2b50 5-Star Rated &middot; Tech &amp; Repair Specialist</span>
    <h1>{copy['h1']}</h1>
    <p>{copy['intro']}</p>
    <a class="btn-primary" href="{DIRECT_BOOKING_URL}">Book Now</a>
    <a class="btn-secondary" href="{BOOKING_URL}">Learn More</a>
  </div>
</div>

<div class="intro-section">
  <p>{copy['services_intro']}</p>
</div>

<div class="services-section">
  <h2>{copy.get('services_header', 'Premium Installation, Tech &amp; Repair Services')}</h2>
  <div class="services-wrap">
{service_items}
  </div>
</div>

<div class="faq-section">
  <h2>Frequently Asked Questions \u2014 {town}, {state}</h2>
{faq_items_html}
</div>

<div class="cta-section">
  <h2>Get a Custom Quote in {town}, {state}</h2>
  <a class="btn-primary" href="{DIRECT_BOOKING_URL}">Book Now</a>
  <a class="btn-secondary" href="{BOOKING_URL}">Learn More</a>
</div>

<footer>
  {BUSINESS_NAME}<br>
  Serving {town}, {state} and all of {county}<br>
  <a class="phone" href="tel:{PHONE}">{PHONE}</a>
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
        f'<li><a href="locations/{t["slug"]}/">{t["town"]}, {t["state"]}</a></li>\n'
        for t in published
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Service Areas \u2014 {BUSINESS_NAME}</title>
<meta name="description" content="Starlink installation, smart home, networking, and RV tech services across East Texas, Southwest Arkansas, Northwest Louisiana, and Southeast Oklahoma.">
<style>
body{{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:#fff;color:#1a1a1a;max-width:700px;margin:2rem auto;padding:0 1.5rem;line-height:1.6;}}
a{{color:#0019ff;text-decoration:none;font-weight:600;}}
h1{{color:#111;font-weight:800;}}
ul{{line-height:2;list-style:none;padding:0;}}
li{{border-bottom:1px solid #eee;padding:0.5rem 0;}}
</style>
</head>
<body>
<h1>{BUSINESS_NAME} \u2014 Service Areas</h1>
<p>{len(published)} of {len(towns)} service-area pages published so far.</p>
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
    coords = load_json(COORDS_FILE)

    pending = [t for t in towns if not t.get("published")]
    if not pending:
        print("All towns published. Nothing to do.")
        return

    batch = pending[:PAGES_PER_RUN]
    for town_entry in batch:
        slug = town_entry["slug"]
        town = town_entry["town"]
        state = town_entry["state"]
        geo = coords.get(slug, {})
        county = geo.get("county", f"{state} service area")
        lat = geo.get("lat", "")
        lng = geo.get("lng", "")
        print(f"Generating page for {town}, {state} ({slug})...")

        subset = pick_service_subset(slug, services)
        copy = call_groq(town, state, county, subset)
        html = render_html(town, state, county, lat, lng, slug, copy, subset)

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
