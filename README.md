# Claudia Radar — research edition

A lightweight exposure dashboard for Claudia, the AI popstar from [claudia.gallery](https://claudia.gallery). **This edition includes independently verified research and a daily discovery queue.**

## Deploy to GitHub + Vercel

1. Extract this ZIP and upload **all its contents**, including the hidden `.github` folder, into a new GitHub repository.
2. At [Vercel](https://vercel.com/new), import the repository and click **Deploy**. The included `vercel.json` sets the `dist` output directory. No build command, API keys, or dependencies are needed.
3. In GitHub, open **Actions → Claudia Radar daily discovery → Run workflow** once to run the first sweep. The scheduled workflow then runs daily at **13:00 UTC** (9 a.m. Eastern during daylight saving, 8 a.m. in winter). GitHub sometimes delays scheduled jobs. Scheduled Actions may also be disabled for inactive repositories.
4. Ensure repository Actions are enabled and `GITHUB_TOKEN` has permission to write contents. The workflow requests `contents: write`; repository or organization policies can override it.

When the workflow commits new candidate findings to `dist/data/mentions.json`, Vercel normally deploys that GitHub push automatically. Check the GitHub Actions logs to confirm the collectors were able to reach their sources.

## What's included

- Research-backed verified mentions (Asterisk Magazine, SI(cinema), LessWrong, Hacker News, and secondary coverage) with their source URLs and dates.
- Dashboard, attention timeline, audience tiers, search, filters, and CSV/JSON export.
- A daily no-key collector (`scripts/collect_mentions.py`) querying Google News RSS and Hacker News Algolia, with a capped deduplicated review queue.
- All automatic candidates remain **Needs review / Unclassified** until a human confirms identity, publication, originality and reach. They are excluded from verified/mainstream dashboard counts.
- Manual additions are stored in this browser's `localStorage`; back them up as JSON. Those manual records do **not** sync across devices. Automated and curated feed records are served from the repository.

## Important cautions

- Claudia's name is shared by unrelated people, brands and crypto products. Disambiguate using `claudia.gallery`, `anabology`, her music videos, or verified accounts. Never count a generic 'Claudia' search hit automatically.
- Syndicated summaries of the Asterisk interview are **secondary amplification**, not fresh independent interviews.
- The LBank token listing references `useclaudia.xyz`, a different on-chain platform; it is **not** counted as evidence of mainstream exposure for the popstar.
- The daily collector covers only indexed Google News and Hacker News. It is **not** an exhaustive Reddit, X, Instagram, TikTok or YouTube monitor. Their API/authentication rules can prevent reliable scraping. Source outages may leave the feed unchanged.
- Google News sometimes supplies aggregator links rather than canonical publisher links. Open every candidate and log the actual original source when verifying.
- A raw view count isn't proof of individual recognition or mainstream penetration.

## Local preview and tests

Run `python -m http.server 8000 --directory dist` and visit `http://localhost:8000` (serving via HTTP is necessary for the JSON feed). Run `python -m unittest discover -s scripts -p 'test_*.py'` for collector tests. You can manually refresh the feed with `python scripts/collect_mentions.py` when the sources are reachable.
