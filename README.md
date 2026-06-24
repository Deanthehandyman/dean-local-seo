# Dean's Handyman Service \u2014 Local SEO Site

Auto-generates and publishes town-specific landing pages for your 200-mile
service area, grounded against your real, live Square catalog (23 current
services, pulled June 2026 \u2014 no plumbing/carpentry, matches your current
Starlink/networking/smart home/RV niche).

45 towns across East Texas, Southwest Arkansas, Northwest Louisiana, and
Southeast Oklahoma. 2 new pages publish every Monday automatically. Full
rollout takes about 6 months at that pace \u2014 you can speed it up any time
by changing `PAGES_PER_RUN` in the workflow file, or running it manually.

## What's in this folder

- `towns.json` \u2014 the 45-town list and publish status (auto-updated by the script)
- `services.json` \u2014 your live Square services, used to ground page copy (no hallucinated services/pricing)
- `locations/` \u2014 where generated pages land (empty until first run)
- `scripts/generate_page.py` \u2014 the generator. Calls Groq, writes grounded copy, renders the page.
- `scripts/ping_indexnow.py` \u2014 notifies Bing/IndexNow after each run so new pages get crawled fast.
- `.github/workflows/generate-pages.yml` \u2014 the cron job. Runs every Monday, generates 2 pages, commits, pushes.
- `0acf2d8096324058e815327524685b4c.txt` \u2014 IndexNow verification file. Don't delete or rename it.
- `sitemap.xml` / `index.html` \u2014 auto-generated once you run it; submit the sitemap to Search Console.

## One-time setup (about 15 minutes)

You're already logged into both GitHub and Netlify, so this should be quick.

### 1. Push this to a new GitHub repo

Open a terminal on your computer, `cd` into this folder, then:

```
git init
git add -A
git commit -m "Initial local SEO site"
git branch -M main
```

Go to https://github.com/new, create a new repo (any name, e.g. `dean-local-seo`),
**don't** initialize it with a README. Then:

```
git remote add origin https://github.com/Deanthehandyman/dean-local-seo.git
git push -u origin main
```

(Replace the URL with the one GitHub shows you after creating the repo.)

### 2. Get a free Groq API key

Go to https://console.groq.com/keys \u2014 sign in, create a key. Free tier easily
covers 2 pages/week.

### 3. Connect Netlify first (so you have the URL for step 4)

- Go to https://app.netlify.com \u2014 you're already logged in via GitHub.
- Click **Add new site \u2192 Import an existing project \u2192 Deploy with GitHub**.
- Pick the repo you just created.
- Build command: leave blank. Publish directory: leave as `/` (or blank).
- Click **Deploy**. Netlify gives you a URL like `https://random-name-123.netlify.app`.
- Optional: in Site settings \u2192 Change site name, give it something readable, e.g. `dean-coverage.netlify.app`.
- Copy that final URL \u2014 you need it for the next step.

### 4. Add GitHub repo secrets

In your new repo on GitHub: **Settings \u2192 Secrets and variables \u2192 Actions \u2192 New repository secret**.
Add these three:

| Secret name | Value |
|---|---|
| `GROQ_API_KEY` | the key from step 2 |
| `SITE_URL` | your Netlify URL from step 3, e.g. `https://dean-coverage.netlify.app` (no trailing slash) |
| `INDEXNOW_KEY` | `0acf2d8096324058e815327524685b4c` (already matches the .txt file in this repo) |

### 5. Test it manually (don't wait for Monday)

In your GitHub repo: **Actions tab \u2192 "Generate Local SEO Pages" \u2192 Run workflow** button.

After it finishes (about 30-60 seconds), check:
- A new commit appeared with 2 new files under `locations/`
- Netlify auto-redeployed (check the Netlify dashboard \u2014 should show a new deploy)
- Visit `https://your-site/locations/pittsburg-tx/` \u2014 it should be live

### 6. Submit the sitemap to Google Search Console

Once the site is live: Search Console \u2192 Sitemaps \u2192 add
`https://your-site/sitemap.xml`

## Ongoing \u2014 what happens automatically

Every Monday at 8am Central, the workflow generates 2 new town pages using
Groq, commits them, Netlify deploys, and IndexNow is pinged so Bing knows
right away. At 2/week, all 45 towns are live in about 6 months.

To go faster: edit `.github/workflows/generate-pages.yml`, change
`PAGES_PER_RUN` env var (also settable as a repo secret) to a higher number,
or just click "Run workflow" manually a few extra times.

## If something breaks

- **No new pages after a scheduled Monday run**: check the Actions tab for a
  red X \u2014 click it to see the error. Most common cause is a missing or
  expired secret.
- **Groq call fails**: the script has a built-in fallback \u2014 it'll still
  generate a page with solid template copy instead of failing the whole run.
  You'll see a "WARNING: Groq call failed" line in the Action log.
- **Want to regenerate a specific town**: open `towns.json`, set that town's
  `"published"` back to `false`, commit, and run the workflow manually.
