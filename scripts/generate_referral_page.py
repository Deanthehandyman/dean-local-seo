#!/usr/bin/env python3
"""
Generates the /starlink-referral/ guide page for Dean's Handyman Service LLC.

This is a standalone informational page with real FAQ content that hosts
the Starlink referral offer and can rank for "starlink referral code" searches.

Run with: python3 scripts/generate_referral_page.py
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = os.environ.get("SITE_URL", "https://deanthehandyman.github.io/dean-local-seo")
BOOKING_URL = "https://deanshandymanservice.square.site"
DIRECT_BOOKING_URL = "https://book.squareup.com/appointments/6adhz5hfnhz08j/location/L1JC5NNCMXS3P/services"
PHONE = "281-917-9914"
BUSINESS_NAME = "Dean's Handyman Service LLC"
BASE_CITY = "Pittsburg, TX"
STARLINK_REFERRAL_URL = "https://www.starlink.com/residential?referral=RC-2034578-19016-61"

OUT_DIR = ROOT / "starlink-referral"

FAQS = [
    {
        "q": "How does the Starlink referral work?",
        "a": (
            "When you use my referral link to order Starlink, both you and I get one free month "
            "of service credit. The credit is applied automatically after your first full billing cycle. "
            "It works for new Residential subscribers only."
        ),
    },
    {
        "q": "Can I use the referral link if I already have Starlink?",
        "a": (
            "No \u2014 the referral only applies to brand-new Starlink accounts. "
            "If you already subscribe, the link won't apply a credit, but I can still "
            "handle your hardware installation, cable routing, or ground pole mount."
        ),
    },
    {
        "q": "Does the referral work with all Starlink plans?",
        "a": (
            "The referral applies to the standard Residential plan. "
            "Business, Maritime, and RV plans are not included in the referral program."
        ),
    },
    {
        "q": "Do I have to book an install through Dean's Handyman to use the referral?",
        "a": (
            "No \u2014 you can use the referral link to order Starlink directly from Starlink's website "
            "without booking an install. The free month is yours either way. "
            "That said, proper mounting and cable routing makes a big difference in signal reliability "
            "and weatherproofing, so many customers book both."
        ),
    },
    {
        "q": "What does a professional Starlink installation include?",
        "a": (
            "A typical install includes roof or pole mounting the dish at the optimal angle, "
            "routing the cable through the wall or conduit, connecting to your router, "
            "and a quick speed test to confirm it's working. "
            "I also advise on the best mounting location based on your roof and tree line."
        ),
    },
    {
        "q": "How do I know if I have a clear sky view for Starlink?",
        "a": (
            "Download the Starlink app and use the obstruction check feature \u2014 "
            "point your phone at different spots on your property. Ideally you want "
            "the northern sky clear of trees and structures. "
            "I can also check during a site visit before you order."
        ),
    },
]


def render_page():
    faq_items_html = "\n".join(
        f"""        <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
          <h3 itemprop="name">{f['q']}</h3>
          <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
            <p itemprop="text">{f['a']}</p>
          </div>
        </div>"""
        for f in FAQS
    )

    faq_schema_items = json.dumps(
        [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in FAQS
        ],
        ensure_ascii=False,
        indent=2,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Starlink Referral Code \u2014 Get a Free Month | {BUSINESS_NAME}</title>
<meta name="description" content="Use this Starlink referral link to get one free month when you sign up. Plus expert installation in East Texas from {BUSINESS_NAME}.">
<link rel="canonical" href="{SITE_URL}/starlink-referral/">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": {faq_schema_items}
}}
</script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #fff; color: #111; line-height: 1.6; }}
  header {{ background: #1a1a2e; color: #fff; padding: 1rem 1.5rem; }}
  header a {{ color: #fff; text-decoration: none; font-weight: 700; font-size: 1.1rem; }}
  .hero {{ background: linear-gradient(135deg, #003d7a 0%, #0099ff 100%); color: #fff; padding: 3rem 1.5rem; text-align: center; }}
  .hero h1 {{ font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 900; margin: 0 0 1rem; }}
  .hero p {{ font-size: 1.1rem; max-width: 600px; margin: 0 auto 1.5rem; opacity: 0.92; }}
  .btn-primary {{ display: inline-block; background: #fff; color: #003d7a; padding: 0.85rem 2rem; border-radius: 4px; text-decoration: none; font-weight: 800; font-size: 1.05rem; margin: 0.25rem; }}
  .btn-secondary {{ display: inline-block; background: transparent; color: #fff; border: 2px solid #fff; padding: 0.8rem 1.75rem; border-radius: 4px; text-decoration: none; font-weight: 700; margin: 0.25rem; }}
  .content {{ max-width: 720px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .content h2 {{ font-size: 1.4rem; font-weight: 800; color: #111; margin: 2rem 0 0.75rem; }}
  .content p {{ margin: 0 0 1rem; color: #333; }}
  .steps {{ list-style: none; padding: 0; margin: 0 0 2rem; counter-reset: steps; }}
  .steps li {{ counter-increment: steps; padding: 0.75rem 0 0.75rem 3rem; border-bottom: 1px solid #eee; position: relative; }}
  .steps li::before {{ content: counter(steps); position: absolute; left: 0; top: 0.75rem; background: #0099ff; color: #fff; width: 1.8rem; height: 1.8rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; }}
  .faq-section {{ max-width: 720px; margin: 0 auto; padding: 0 1.5rem 2.5rem; }}
  .faq-section h2 {{ font-size: 1.4rem; font-weight: 800; margin: 0 0 1.25rem; }}
  .faq-item {{ border-bottom: 1px solid #eee; padding: 1rem 0; }}
  .faq-item h3 {{ font-size: 1rem; font-weight: 700; margin: 0 0 0.4rem; color: #111; }}
  .faq-item p {{ margin: 0; color: #444; font-size: 0.95rem; }}
  .cta-section {{ text-align: center; padding: 2.5rem 1.5rem; background: #f4f5f7; }}
  .cta-section h2 {{ font-size: 1.4rem; font-weight: 800; margin: 0 0 1.25rem; }}
  footer {{ text-align: center; padding: 1.5rem; font-size: 0.85rem; color: #666; border-top: 1px solid #eee; }}
  footer a {{ color: #0099ff; }}
</style>
</head>
<body>
<header>
  <a href="{SITE_URL}/">{BUSINESS_NAME}</a>
</header>

<div class="hero">
  <h1>Get a Free Month of Starlink</h1>
  <p>Use this referral link when you sign up for Starlink Residential \u2014 you get one free month, automatically applied after your first billing cycle.</p>
  <a class="btn-primary" href="{STARLINK_REFERRAL_URL}" target="_blank" rel="noopener">Claim Your Free Month \u2192</a>
  <a class="btn-secondary" href="{DIRECT_BOOKING_URL}">Book Professional Install</a>
</div>

<div class="content">
  <h2>How It Works</h2>
  <p>Starlink's referral program lets existing subscribers share a link with new customers. When you order through the link, both of us get a free month of service. Here's the full process:</p>
  <ol class="steps">
    <li>Click the referral link above \u2014 it takes you directly to Starlink's order page with the referral pre-applied.</li>
    <li>Complete your Starlink order as normal. The referral is attached automatically \u2014 no code to enter.</li>
    <li>After your first full billing cycle, the free month credit is applied to your account.</li>
    <li>Schedule a professional installation so your dish is mounted correctly and oriented for the best signal.</li>
  </ol>
  <h2>Why Professional Installation Matters</h2>
  <p>Roof mounting, cable routing through walls, conduit runs, and ground poles all require tools and experience to do cleanly and weatherproof. A good mount also gets your dish higher and clearer of tree obstructions, which directly improves uptime and speeds.</p>
  <p>{BUSINESS_NAME} handles Starlink installations across East Texas. <a href="{DIRECT_BOOKING_URL}">Book an install here</a> or call <a href="tel:{PHONE}">{PHONE}</a>.</p>
</div>

<div class="faq-section">
  <h2>Frequently Asked Questions</h2>
{faq_items_html}
</div>

<div class="cta-section">
  <h2>Ready to Get Connected?</h2>
  <a class="btn-primary" href="{STARLINK_REFERRAL_URL}" target="_blank" rel="noopener" style="background:#0099ff;color:#fff;">Use Referral Link \u2192</a>
  &nbsp;
  <a class="btn-primary" href="{DIRECT_BOOKING_URL}" style="background:#1a1a2e;color:#fff;">Book Install</a>
</div>

<footer>
  {BUSINESS_NAME} \u2014 Serving {BASE_CITY} and East Texas<br>
  <a href="tel:{PHONE}">{PHONE}</a> &middot; <a href="{SITE_URL}/">Back to home</a>
</footer>
</body>
</html>"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = render_page()
    out_path = OUT_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
