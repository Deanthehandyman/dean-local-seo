#!/usr/bin/env python3
"""
Service detail page generator for Dean's Handyman Service LLC.

Builds one static page per real, bookable Square catalog service into
services/<slug>/index.html, plus a services/index.html directory page.

Unlike generate_page.py (town pages), this does NOT call Groq -- the copy
comes straight from the real Square item descriptions in services_full.json,
since that's already real, specific, professionally-written copy. No AI
paraphrasing needed or wanted here.

Run with: python3 scripts/generate_service_pages.py
Re-run any time services_full.json is updated (e.g. after refreshing it from
the live Square catalog).
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICES_FULL_FILE = ROOT / "services_full.json"
SERVICES_DIR = ROOT / "services"
SITE_URL = os.environ.get("SITE_URL", "https://deanthehandyman.github.io/dean-local-seo")
BOOKING_URL = "https://deanshandymanservice.square.site"
DIRECT_BOOKING_URL = "https://book.squareup.com/appointments/6adhz55czkh9i7/location/LRQVC65X9CQJK/services?buttonTextColor=ffffff&color=0019ff&locale=en&referrer=so&team_member_id=TM41qxXARrQWpS86"

PHONE = "281-917-9914"
BUSINESS_NAME = "Dean's Handyman Service LLC"
BASE_CITY = "Pittsburg, TX"

CATEGORY_ORDER = [
    "Starlink & Connectivity",
    "Networking & Wi-Fi",
    "Smart Home & Security",
    "Electrical Services",
    "Home Theater & Mounting",
    "RV Services",
    "General Services",
]
STARLINK_REFERRAL_URL = "https://www.starlink.com/residential?referral=RC-2034578-19016-61"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def extract_faqs(text):
    """Pull Q&A pairs out of a 'Frequently Asked Questions' paragraph for schema use."""
    for para in text.split("\n\n"):
        lines = para.strip().split("\n")
        if lines[0].strip().lower().startswith("frequently asked questions"):
            qa_lines = lines[1:]
            faqs = []
            i = 0
            while i < len(qa_lines) - 1:
                q, a = qa_lines[i].strip(), qa_lines[i + 1].strip()
                if q and a:
                    faqs.append({"q": q, "a": a})
                i += 2
            return faqs
    return []


def nl2br_paragraphs(text):
    """Convert plain-text description into HTML. Paragraphs are split on blank
    lines. A paragraph that starts with 'Frequently Asked Questions' is detected
    and rendered as a proper Q&A list (alternating question/answer lines) instead
    of one wall of text with <br> tags."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    html_parts = []
    for p in paragraphs:
        lines = p.split("\n")
        if lines[0].strip().lower().startswith("frequently asked questions"):
            qa_lines = lines[1:]
            faq_items = []
            i = 0
            while i < len(qa_lines) - 1:
                q = qa_lines[i].strip()
                a = qa_lines[i + 1].strip()
                if q and a:
                    faq_items.append(f'<div class="faq-item"><h3>{q}</h3><p>{a}</p></div>')
                i += 2
            if faq_items:
                html_parts.append(
                    '<h2 class="faq-heading">Frequently Asked Questions</h2>\n'
                    + "\n".join(faq_items)
                )
                continue
        p_html = p.replace("\n", "<br>")
        html_parts.append(f"<p>{p_html}</p>")
    return "\n".join(html_parts)


def meta_description_from(desc, name):
    """First sentence or ~155 chars, whichever is shorter, for the meta tag."""
    first_para = desc.split("\n\n")[0].strip()
    first_sentence = re.split(r"(?<=[.!?])\s", first_para)[0]
    candidate = first_sentence if first_sentence else first_para
    if len(candidate) > 155:
        candidate = candidate[:152].rsplit(" ", 1)[0] + "..."
    return candidate or f"{name} from {BUSINESS_NAME}. Call {PHONE}."




def should_show_referral(service):
    """Return True for Starlink/connectivity services that show the referral callout."""
    REFERRAL_SLUGS = {
        "starlink-installation",
        "ground-pole-mount",
        "virtual-consultation",
        "rv-connectivity-bundle",
    }
    return service.get("slug", "") in REFERRAL_SLUGS


def render_service_html(service, related):
    name = service["name"]
    slug = service["slug"]
    category = service["category"]
    desc = service["description"] or f"{name} from {BUSINESS_NAME}, certified and based in {BASE_CITY}."
    price = service.get("price")
    duration = service.get("duration_minutes")
    meta_desc = meta_description_from(desc, name)
    title = f"{name} | {BUSINESS_NAME}"
    desc_html = nl2br_paragraphs(desc)
    faqs = extract_faqs(desc)

    facts = []
    if price:
        facts.append(f'<div class="fact"><span class="fact-label">Starting at</span><span class="fact-value">{price}</span></div>')
    if duration:
        facts.append(f'<div class="fact"><span class="fact-label">Typical duration</span><span class="fact-value">{duration} min</span></div>')
    facts.append(f'<div class="fact"><span class="fact-label">Service area</span><span class="fact-value">200-mi radius of {BASE_CITY}</span></div>')
    facts_html = "\n".join(facts)

    related_html = ""
    if related:
        related_items = "\n".join(
            f'<li><a href="../{r["slug"]}/">{r["name"]}</a></li>' for r in related
        )
        related_html = f"""
<div class="related-section">
  <h2>Related Services</h2>
  <ul class="related-list">
{related_items}
  </ul>
</div>"""

    referral_html = ""
    if should_show_referral(service):
        referral_html = (
            '<div class="referral-block">\n'
            '  <h2>Get a Free Month of Starlink</h2>\n'
            '  <p>New Starlink customer? Use my referral link when you sign up and '
            '<strong>get one free month</strong> \u2014 no extra cost to you.</p>\n'
            f'  <a class="btn-referral" href="{STARLINK_REFERRAL_URL}" '
            'target="_blank" rel="noopener">Claim Your Free Month \u2192</a>\n'
            '</div>'
        )


    service_schema = f"""{{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": {json.dumps(name)},
  "description": {json.dumps(meta_desc)},
  "areaServed": {{"@type": "AdministrativeArea", "name": "East Texas, Southwest Arkansas, Northwest Louisiana, Southeast Oklahoma"}},
  "provider": {{
    "@type": "LocalBusiness",
    "name": {json.dumps(BUSINESS_NAME)},
    "telephone": {json.dumps(PHONE)}
  }}{f',\n  "offers": {{"@type": "Offer", "priceCurrency": "USD", "price": "{price.replace("$","")}"}}' if price else ""}
}}"""

    breadcrumb_schema = f"""{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Home", "item": "{SITE_URL}/"}},
    {{"@type": "ListItem", "position": 2, "name": "Services", "item": "{SITE_URL}/services/"}},
    {{"@type": "ListItem", "position": 3, "name": {json.dumps(name)}, "item": "{SITE_URL}/services/{slug}/"}}
  ]
}}"""

    faq_schema_block = ""
    if faqs:
        faq_entities = ",\n".join(
            f"""    {{
      "@type": "Question",
      "name": {json.dumps(f['q'])},
      "acceptedAnswer": {{"@type": "Answer", "text": {json.dumps(f['a'])}}}
    }}"""
            for f in faqs
        )
        faq_schema_block = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{faq_entities}
  ]
}}
</script>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{SITE_URL}/services/{slug}/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0019ff">
<script type="application/ld+json">
{service_schema}
</script>
<script type="application/ld+json">
{breadcrumb_schema}
</script>{faq_schema_block}
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
  .topbar .brand {{ font-weight: 700; font-size: 1.05rem; color: #1a1a1a; text-decoration: none; }}
  .topbar .call-btn {{
    background: #0019ff;
    color: #fff;
    border-radius: 999px;
    padding: 0.55rem 1.3rem;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none;
  }}
  .breadcrumb {{
    max-width: 720px;
    margin: 0 auto;
    padding: 0 1.5rem;
    font-size: 0.85rem;
    color: #777;
  }}
  .breadcrumb a {{ color: #0019ff; text-decoration: none; }}
  .hero {{
    background: #0a0e1a;
    color: #fff;
    padding: 2.25rem 1.5rem 2rem;
  }}
  .hero-inner {{
    max-width: 720px;
    margin: 0 auto;
  }}
  .hero .eyebrow {{
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.6rem;
    color: #6e8bff;
  }}
  .hero h1 {{
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0 0 0.75rem;
    line-height: 1.2;
  }}
  .facts-row {{
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-top: 1.25rem;
  }}
  .fact {{
    display: flex;
    flex-direction: column;
  }}
  .fact-label {{
    font-size: 0.75rem;
    color: #9aa6c4;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }}
  .fact-value {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
  }}
  .btn-primary {{
    display: inline-block;
    text-align: center;
    background: #0019ff;
    color: #fff;
    padding: 0.95rem 2rem;
    border-radius: 999px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 1.5rem;
    font-size: 1.02rem;
  }}
  .btn-secondary {{
    display: inline-block;
    text-align: center;
    background: transparent;
    color: #fff;
    border: 2px solid #fff;
    padding: 0.85rem 1.75rem;
    border-radius: 999px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 1.5rem;
    margin-left: 0.75rem;
    font-size: 1.02rem;
  }}
  .content-section {{
    max-width: 720px;
    margin: 0 auto;
    padding: 2.25rem 1.5rem;
  }}
  .content-section p {{
    color: #2a2a2a;
    margin: 0 0 1.1rem;
  }}
  .faq-heading {{
    font-size: 1.25rem;
    font-weight: 800;
    color: #111;
    margin: 1.75rem 0 1rem;
  }}
  .faq-item {{
    margin-bottom: 1.25rem;
  }}
  .faq-item h3 {{
    font-size: 1rem;
    font-weight: 700;
    color: #111;
    margin: 0 0 0.3rem;
  }}
  .faq-item p {{
    margin: 0;
    color: #444;
    font-size: 0.95rem;
  }}
  .cta-section {{
    text-align: center;
    padding: 2.5rem 1.5rem;
    background: #f4f5f7;
  }}
  .cta-section h2 {{
    font-size: 1.4rem;
    font-weight: 800;
    margin: 0 0 1.25rem;
    color: #111;
  }}
  .related-section {{
    max-width: 720px;
    margin: 0 auto;
    padding: 0 1.5rem 2.5rem;
  }}
  .related-section h2 {{
    font-size: 1.2rem;
    font-weight: 800;
    margin: 0 0 1rem;
    color: #111;
  }}
  .related-list {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  .related-list li {{
    border-bottom: 1px solid #eee;
    padding: 0.6rem 0;
  }}
  .related-list a {{
    color: #0019ff;
    text-decoration: none;
    font-weight: 600;
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
  @media (max-width: 480px) {{
    .btn-secondary {{ margin-left: 0; display: block; margin-top: 0.75rem; max-width: 280px; }}
    .btn-primary {{ display: block; max-width: 280px; }}
  }}
</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="../../">{BUSINESS_NAME}</a>
  <a class="call-btn" href="tel:{PHONE}">Call Now</a>
</div>

<div class="breadcrumb">
  <a href="../../">Home</a> &rsaquo; <a href="../">Services</a> &rsaquo; {name}
</div>

<div class="hero">
  <div class="hero-inner">
    <span class="eyebrow">{category}</span>
    <h1>{name}</h1>
    <div class="facts-row">
{facts_html}
    </div>
    <a class="btn-primary" href="{DIRECT_BOOKING_URL}">Book This Service</a>
    <a class="btn-secondary" href="tel:{PHONE}">Call {PHONE}</a>
  </div>
</div>

<div class="content-section">
{desc_html}
</div>
{referral_html}

<div class="cta-section">
  <h2>Ready to get started?</h2>
  <a class="btn-primary" href="{DIRECT_BOOKING_URL}" style="color:#fff;">Book {name}</a>
</div>
{related_html}

<footer>
  {BUSINESS_NAME}<br>
  Serving East Texas, Southwest Arkansas, Northwest Louisiana &amp; Southeast Oklahoma<br>
  <a class="phone" href="tel:{PHONE}">{PHONE}</a>
</footer>
</body>
</html>
"""


def render_directory_html(services_by_category):
    sections = []
    for cat in CATEGORY_ORDER:
        items = services_by_category.get(cat)
        if not items:
            continue
        cards = "\n".join(
            f"""    <a class="service-card" href="{s['slug']}/">
      <h3>{s['name']}</h3>
      <p>{(s['description'][:110] + '...') if s['description'] and len(s['description']) > 110 else (s['description'] or '')}</p>
      {f'<span class="price-tag">{s["price"]}</span>' if s.get('price') else ''}
    </a>"""
            for s in items
        )
        sections.append(f"""
  <div class="category-block">
    <h2>{cat}</h2>
    <div class="card-grid">
{cards}
    </div>
  </div>""")

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>All Services | {BUSINESS_NAME}</title>
<meta name="description" content="Starlink installation, smart home, networking, electrical, and RV tech services across East Texas, Southwest Arkansas, Northwest Louisiana, and Southeast Oklahoma.">
<link rel="canonical" href="{SITE_URL}/services/">
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
    max-width: 1000px;
    margin: 0 auto;
  }}
  .topbar .brand {{ font-weight: 700; font-size: 1.05rem; color: #1a1a1a; text-decoration: none; }}
  .topbar .call-btn {{
    background: #0019ff;
    color: #fff;
    border-radius: 999px;
    padding: 0.55rem 1.3rem;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none;
  }}
  .page-hero {{
    text-align: center;
    padding: 1.5rem 1.5rem 2.5rem;
    max-width: 700px;
    margin: 0 auto;
  }}
  .page-hero h1 {{ font-size: 2rem; font-weight: 800; margin: 0 0 0.5rem; }}
  .page-hero p {{ color: #555; }}
  .category-block {{
    max-width: 1000px;
    margin: 0 auto;
    padding: 1.5rem 1.5rem 0.5rem;
  }}
  .category-block h2 {{
    font-size: 1.3rem;
    font-weight: 800;
    color: #0019ff;
    margin: 0 0 1rem;
    border-bottom: 2px solid #f0f0f0;
    padding-bottom: 0.5rem;
  }}
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }}
  .service-card {{
    display: block;
    border: 1px solid #eee;
    border-radius: 12px;
    padding: 1.1rem;
    text-decoration: none;
    color: inherit;
    transition: box-shadow 0.15s, border-color 0.15s;
  }}
  .service-card:hover {{
    border-color: #0019ff;
    box-shadow: 0 2px 10px rgba(0,25,255,0.08);
  }}
  .service-card h3 {{
    margin: 0 0 0.4rem;
    font-size: 1.02rem;
    color: #111;
  }}
  .service-card p {{
    margin: 0 0 0.5rem;
    font-size: 0.88rem;
    color: #555;
  }}
  .price-tag {{
    font-size: 0.85rem;
    font-weight: 700;
    color: #0019ff;
  }}
  footer {{
    text-align: center;
    padding: 2rem 1.5rem;
    font-size: 0.85rem;
    color: #777;
    background: #fafafa;
    border-top: 1px solid #eee;
    margin-top: 2rem;
  }}
  footer .phone {{ color: #0019ff; font-weight: 600; text-decoration: none; }}

  .referral-block {
    max-width: 720px;
    margin: 0 auto 2rem;
    padding: 1.5rem;
    background: #e8f4fd;
    border: 2px solid #0099ff;
    border-radius: 8px;
    text-align: center;
  }
  .referral-block h2 {
    font-size: 1.3rem;
    font-weight: 800;
    color: #003d7a;
    margin: 0 0 0.75rem;
  }
  .referral-block p {
    color: #333;
    margin: 0 0 1rem;
    font-size: 0.95rem;
  }
  .referral-block .btn-referral {
    display: inline-block;
    background: #0099ff;
    color: #fff;
    padding: 0.7rem 1.5rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 700;
    font-size: 1rem;
  }
  .referral-block .btn-referral:hover {
    background: #0077cc;
  }</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="../">{BUSINESS_NAME}</a>
  <a class="call-btn" href="tel:{PHONE}">Call Now</a>
</div>

<div class="page-hero">
  <h1>All Services</h1>
  <p>Certified Starlink installation, smart home tech, networking, electrical, and RV systems work across the {BUSINESS_NAME} service area.</p>
</div>
{sections_html}

<footer>
  {BUSINESS_NAME}<br>
  Serving East Texas, Southwest Arkansas, Northwest Louisiana &amp; Southeast Oklahoma<br>
  <a class="phone" href="tel:{PHONE}">{PHONE}</a>
</footer>
</body>
</html>
"""


def main():
    services = load_json(SERVICES_FULL_FILE)
    SERVICES_DIR.mkdir(parents=True, exist_ok=True)

    by_category = {}
    for s in services:
        by_category.setdefault(s["category"], []).append(s)

    for s in services:
        same_category = [r for r in by_category.get(s["category"], []) if r["slug"] != s["slug"]]
        related = same_category[:4]
        html = render_service_html(s, related)
        page_dir = SERVICES_DIR / s["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        with open(page_dir / "index.html", "w") as f:
            f.write(html)
        print(f"  -> wrote services/{s['slug']}/index.html")

    dir_html = render_directory_html(by_category)
    with open(SERVICES_DIR / "index.html", "w") as f:
        f.write(dir_html)
    print(f"  -> wrote services/index.html (directory page)")

    print(f"Done. {len(services)} service page(s) generated.")


if __name__ == "__main__":
    main()
