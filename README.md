# Claudia Radar — research edition

A lightweight exposure dashboard for Claudia, the AI popstar from [claudia.gallery](https://claudia.gallery). **This edition includes independently verified research and a daily discovery queue.**

**In progress · fan-made · unofficial.** Not affiliated with Claudia, anabology, Anthropic, claudia.gallery, or any associated token or studio. Not financial advice.

## Deploy to GitHub + Vercel

1. Push this repository to GitHub (or open it in GitHub Desktop and publish).
2. At [Vercel](https://vercel.com/new), import the repository and click **Deploy**. The included `vercel.json` sets the `dist` output directory. No build command or app dependencies are needed.
3. In GitHub, open **Actions → Claudia Radar daily discovery → Run workflow** once to run the first sweep. The scheduled workflow then runs daily at **13:00 UTC** (9 a.m. Eastern during daylight saving, 8 a.m. in winter). GitHub sometimes delays scheduled jobs. Scheduled Actions may also be disabled for inactive repositories.
4. Ensure repository Actions are enabled and `GITHUB_TOKEN` can write contents. The workflow requests `contents: write`; repository or organization policies can override it.

When the workflow commits new candidate findings to `dist/data/mentions.json`, Vercel normally deploys that GitHub push automatically. Check the GitHub Actions logs to confirm which collectors succeeded.

## Optional free API keys (more coverage)

No keys are required for Google News, Hacker News, Bluesky, or GDELT. Add these **GitHub → Settings → Secrets and variables → Actions** secrets to unlock more channels:

| Secret | Free signup |
| --- | --- |
| `NEWSDATA_API_KEY` | [newsdata.io](https://newsdata.io) free tier — copy from your dashboard (Vercel will not export the real value from Mainstream Meter) |
| `APIFY_TOKEN` | [apify.com](https://apify.com) free tier — copy from your Apify console Settings → Integrations |
| `YOUTUBE_API_KEY` | Google Cloud Console → enable **YouTube Data API v3** → create an API key |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → create an app |
| `PODCASTINDEX_KEY` + `PODCASTINDEX_SECRET` | [api.podcastindex.org](https://api.podcastindex.org) → request a free key |

Missing secrets just skip that source. The rest of the sweep still runs.

## What's included

- Research-backed verified mentions (Asterisk Magazine, SI(cinema), LessWrong, Hacker News, and secondary coverage) with their source URLs and dates.
- Dashboard, attention timeline, audience tiers, search, filters, and CSV/JSON export.
- A daily collector (`scripts/collect_mentions.py`) querying:
  - **Always on:** Google News RSS, Hacker News Algolia, Bluesky public search, GDELT DOC
  - **With free keys:** YouTube Data API, Reddit OAuth search, Podcast Index
- All automatic candidates remain **Needs review / Unclassified** until a human confirms identity, publication, originality and reach. They are excluded from verified/mainstream dashboard counts.
- Manual additions are stored in this browser's `localStorage`; back them up as JSON. Those manual records do **not** sync across devices. Automated and curated feed records are served from the repository.

## Important cautions

- Claudia's name is shared by unrelated people, brands and crypto products. Disambiguate using `claudia.gallery`, `anabology`, her music videos, or verified accounts. Never count a generic 'Claudia' search hit automatically.
- Syndicated summaries of the Asterisk interview are **secondary amplification**, not fresh independent interviews.
- The LBank token listing references `useclaudia.xyz`, a different on-chain platform; it is **not** counted as evidence of mainstream exposure for the popstar.
- X, Instagram, and TikTok are **not** monitored (no usable free search API for this project). Source outages may leave the feed unchanged for that channel.
- Google News sometimes supplies aggregator links rather than canonical publisher links. Open every candidate and log the actual original source when verifying.
- A raw view count isn't proof of individual recognition or mainstream penetration.

## Local preview and tests

If you have Python locally: serve with `python -m http.server 8000 --directory dist` and visit `http://localhost:8000`. Run collector tests with `python -m unittest discover -s scripts -p 'test_*.py'`. Otherwise rely on GitHub Actions + the live Vercel deploy — no local server required.
