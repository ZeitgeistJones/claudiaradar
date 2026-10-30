#!/usr/bin/env python3
"""Daily public-source discovery for Claudia Radar.

No third-party packages. No-key sources always run.
Optional free API keys via env unlock YouTube, Reddit, and Podcast Index.
"""
from __future__ import annotations

from base64 import b64encode
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET

DEST = Path(__file__).resolve().parents[1] / 'dist' / 'data' / 'mentions.json'
USER_AGENT = 'ClaudiaRadar/1.1 (research bot; +https://github.com/ZeitgeistJones/claudiaradar)'
CANDIDATE_CAP = 250

# Precise phrases only — bare "Claudia" floods false positives.
TERMS = [
    '"claudia.gallery"',
    '"Claudia" "anabology"',
    '"claudia_popstar"',
    '"claudiathepopstar"',
    '"slopcore" Claudia',
    '"AI popstar" Claudia',
    '"AI pop star" Claudia',
]

STRONG_MARKERS = (
    'claudia.gallery',
    'claudia_popstar',
    'claudiathepopstar',
)
SOFT_MARKERS = (
    'anabology',
    'slopcore',
    'ai popstar',
    'ai pop star',
    'claude music video',
    'ai character claudia',
)


def env(name: str) -> str:
    return (os.environ.get(name) or '').strip()


def fetch(url: str, headers: dict | None = None, data: bytes | None = None) -> bytes:
    hdrs = {'User-Agent': USER_AGENT, 'Accept': '*/*'}
    if headers:
        hdrs.update(headers)
    req = Request(url, headers=hdrs, data=data, method='POST' if data is not None else 'GET')
    with urlopen(req, timeout=20) as res:
        return res.read(2_000_000)


def fetch_json(url: str, headers: dict | None = None, data: bytes | None = None) -> dict | list:
    raw = fetch(url, headers=headers, data=data)
    return json.loads(raw.decode('utf-8', errors='replace'))


def relevant(title: str, description: str = '') -> bool:
    text = re.sub(r'<[^>]*>', ' ', f'{title} {description}').lower()
    if any(marker in text for marker in STRONG_MARKERS):
        return True
    return 'claudia' in text and any(marker in text for marker in SOFT_MARKERS)


def canonical(url: str) -> str:
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), '', ''))


def record(title: str, url: str, day: str, outlet: str, category: str) -> dict:
    ident = hashlib.sha256(canonical(url).encode()).hexdigest()[:16]
    return {
        'id': 'candidate-' + ident,
        'title': title[:180],
        'url': url,
        'date': day,
        'outlet': outlet[:80],
        'category': category,
        'tier': 'Unclassified',
        'origin': 'Unclassified',
        'verification': 'Needs review',
        'notes': (
            'Automatically discovered. Confirm identity, publisher, date and '
            'uniqueness before counting.'
        ),
    }


def iso_day(value: str | None, fallback: str | None = None) -> str | None:
    if value:
        day = str(value)[:10]
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
            return day
        try:
            return parsedate_to_datetime(value).date().isoformat()
        except (ValueError, TypeError, IndexError):
            pass
        # GDELT style: 20261028T123045Z
        m = re.match(r'^(\d{4})(\d{2})(\d{2})', value)
        if m:
            return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
        except ValueError:
            pass
    return fallback or datetime.now(timezone.utc).date().isoformat()


def news() -> list[dict]:
    found: list[dict] = []
    for term in TERMS:
        url = 'https://news.google.com/rss/search?' + urlencode({
            'q': term,
            'hl': 'en-US',
            'gl': 'US',
            'ceid': 'US:en',
        })
        root = ET.fromstring(fetch(url))
        for item in root.findall('.//item'):
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            desc = item.findtext('description') or ''
            if not link.startswith('http') or not relevant(title, desc):
                continue
            day = iso_day(item.findtext('pubDate'))
            outlet = (item.findtext('source') or 'Google News').strip() or 'Google News'
            found.append(record(title, link, day, outlet, 'News'))
    return found


def hacker_news() -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for term in TERMS:
        url = 'https://hn.algolia.com/api/v1/search_by_date?' + urlencode({
            'query': term.strip('"'),
            'tags': 'story,comment',
            'hitsPerPage': 50,
        })
        hits = fetch_json(url).get('hits', [])
        for hit in hits:
            title = hit.get('title') or hit.get('story_title') or 'Hacker News mention of Claudia'
            body = hit.get('comment_text') or hit.get('story_text') or ''
            if not relevant(title, body):
                continue
            obj = hit.get('objectID')
            day = iso_day(hit.get('created_at'))
            if not obj or not day:
                continue
            link = 'https://news.ycombinator.com/item?id=' + str(obj)
            if link in seen:
                continue
            seen.add(link)
            found.append(record(title, link, day, 'Hacker News', 'Forums'))
    return found


def bluesky() -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        'claudia.gallery',
        'claudia_popstar',
        'claudiathepopstar',
        'slopcore Claudia',
        'AI popstar Claudia',
    ]
    for q in queries:
        url = 'https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?' + urlencode({
            'q': q,
            'limit': 40,
        })
        posts = fetch_json(url).get('posts', [])
        for post in posts:
            author = (post.get('author') or {}).get('handle') or 'Bluesky'
            record_body = post.get('record') or {}
            text = record_body.get('text') or ''
            uri = post.get('uri') or ''
            if not uri.startswith('at://') or not relevant(text, q):
                continue
            # at://did:plc:xxx/app.bsky.feed.post/abc -> https://bsky.app/profile/handle/post/abc
            parts = uri.split('/')
            rkey = parts[-1] if parts else ''
            link = f'https://bsky.app/profile/{author}/post/{rkey}'
            if link in seen:
                continue
            seen.add(link)
            day = iso_day(record_body.get('createdAt'))
            title = (text[:140] + '…') if len(text) > 140 else (text or 'Bluesky post about Claudia')
            found.append(record(title, link, day, f'Bluesky @{author}', 'Social'))
    return found


def gdelt() -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        'claudia.gallery',
        '"claudia_popstar"',
        '"AI popstar" Claudia',
        'slopcore Claudia',
        'anabology Claudia',
    ]
    for q in queries:
        url = 'https://api.gdeltproject.org/api/v2/doc/doc?' + urlencode({
            'query': q,
            'mode': 'ArtList',
            'format': 'json',
            'maxrecords': '50',
            'sort': 'DateDesc',
        })
        try:
            payload = fetch_json(url)
        except json.JSONDecodeError:
            # GDELT sometimes returns plain text errors
            continue
        if not isinstance(payload, dict):
            continue
        for article in payload.get('articles') or []:
            title = (article.get('title') or '').strip()
            link = (article.get('url') or '').strip()
            domain = (article.get('domain') or 'GDELT').strip()
            if not link.startswith('http') or not relevant(title, q):
                continue
            if canonical(link) in seen:
                continue
            seen.add(canonical(link))
            day = iso_day(article.get('seendate'))
            found.append(record(title or link, link, day, domain, 'News'))
        time.sleep(1)  # be polite to GDELT
    return found


def youtube() -> list[dict]:
    key = env('YOUTUBE_API_KEY')
    if not key:
        raise RuntimeError('skipped: no YOUTUBE_API_KEY')
    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        'claudia.gallery',
        'claudia_popstar',
        'claudiathepopstar',
        'Claudia AI popstar',
        'Claudia slopcore',
        'Claudia anabology',
    ]
    for q in queries:
        url = 'https://www.googleapis.com/youtube/v3/search?' + urlencode({
            'part': 'snippet',
            'type': 'video',
            'maxResults': 15,
            'q': q,
            'key': key,
        })
        items = fetch_json(url).get('items', [])
        for item in items:
            video_id = ((item.get('id') or {}).get('videoId') or '').strip()
            snip = item.get('snippet') or {}
            title = (snip.get('title') or '').strip()
            desc = snip.get('description') or ''
            channel = (snip.get('channelTitle') or 'YouTube').strip()
            if not video_id or not relevant(title, desc + ' ' + q):
                continue
            link = 'https://www.youtube.com/watch?v=' + video_id
            if link in seen:
                continue
            seen.add(link)
            day = iso_day(snip.get('publishedAt'))
            found.append(record(title, link, day, channel, 'Video / podcast'))
    return found


def reddit() -> list[dict]:
    client_id = env('REDDIT_CLIENT_ID')
    client_secret = env('REDDIT_CLIENT_SECRET')
    if not client_id or not client_secret:
        raise RuntimeError('skipped: no REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET')

    basic = b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    token_payload = urlencode({'grant_type': 'client_credentials'}).encode()
    token_data = fetch_json(
        'https://www.reddit.com/api/v1/access_token',
        headers={
            'Authorization': f'Basic {basic}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': USER_AGENT,
        },
        data=token_payload,
    )
    access = token_data.get('access_token')
    if not access:
        raise RuntimeError('Reddit token missing')

    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        'claudia.gallery',
        'claudia_popstar',
        'claudiathepopstar',
        'Claudia slopcore',
        'Claudia AI popstar',
        'Claudia anabology',
    ]
    for q in queries:
        url = 'https://oauth.reddit.com/search?' + urlencode({
            'q': q,
            'sort': 'new',
            'limit': 25,
            't': 'year',
            'type': 'link',
        })
        children = (fetch_json(url, headers={
            'Authorization': f'Bearer {access}',
            'User-Agent': USER_AGENT,
        }).get('data') or {}).get('children') or []
        for child in children:
            data = child.get('data') or {}
            title = (data.get('title') or '').strip()
            selftext = data.get('selftext') or ''
            permalink = (data.get('permalink') or '').strip()
            sub = (data.get('subreddit_name_prefixed') or 'Reddit').strip()
            if not permalink or not relevant(title, selftext + ' ' + q):
                continue
            link = 'https://www.reddit.com' + permalink
            if link in seen:
                continue
            seen.add(link)
            created = data.get('created_utc')
            if isinstance(created, (int, float)):
                day = datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat()
            else:
                day = iso_day(None)
            found.append(record(title, link, day, sub, 'Forums'))
    return found


def podcast_index() -> list[dict]:
    api_key = env('PODCASTINDEX_KEY')
    api_secret = env('PODCASTINDEX_SECRET')
    if not api_key or not api_secret:
        raise RuntimeError('skipped: no PODCASTINDEX_KEY / PODCASTINDEX_SECRET')

    epoch = str(int(time.time()))
    auth = hashlib.sha1((api_key + api_secret + epoch).encode('utf-8')).hexdigest()
    headers = {
        'User-Agent': USER_AGENT,
        'X-Auth-Key': api_key,
        'X-Auth-Date': epoch,
        'Authorization': auth,
    }

    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        'claudia.gallery',
        'claudia popstar',
        'claudia slopcore',
        'claudia anabology',
        'AI popstar Claudia',
    ]
    for q in queries:
        url = 'https://api.podcastindex.org/api/1.0/search/byterm?' + urlencode({
            'q': q,
            'max': 20,
        })
        feeds = fetch_json(url, headers=headers).get('feeds') or []
        for feed in feeds:
            title = (feed.get('title') or '').strip()
            desc = (feed.get('description') or '') + ' ' + (feed.get('author') or '')
            link = (feed.get('link') or feed.get('url') or '').strip()
            if not link.startswith('http') or not relevant(title, desc + ' ' + q):
                continue
            if canonical(link) in seen:
                continue
            seen.add(canonical(link))
            day = iso_day(None)
            newest = feed.get('newestItemPublishTime')
            if isinstance(newest, (int, float)) and newest > 0:
                day = datetime.fromtimestamp(newest, tz=timezone.utc).date().isoformat()
            outlet = (feed.get('author') or feed.get('ownerName') or 'Podcast Index').strip()
            found.append(record(title, link, day, outlet, 'Video / podcast'))
    return found


def merge(data: dict, new: list[dict], now: str) -> dict:
    seen = {canonical(x['url']) for x in data.get('verified', []) if x.get('url')}
    candidates: list[dict] = []
    for x in new + data.get('candidates', []):
        url = x.get('url', '')
        if not url.startswith(('https://', 'http://')) or canonical(url) in seen:
            continue
        seen.add(canonical(url))
        x.update(verification='Needs review', tier='Unclassified', origin='Unclassified')
        candidates.append(x)
    data['candidates'] = sorted(candidates, key=lambda x: x.get('date', ''), reverse=True)[:CANDIDATE_CAP]
    data['updatedAt'] = now
    return data


SOURCES = [
    ('Google News', news),
    ('Hacker News', hacker_news),
    ('Bluesky', bluesky),
    ('GDELT', gdelt),
    ('YouTube', youtube),
    ('Reddit', reddit),
    ('Podcast Index', podcast_index),
]


def main() -> None:
    data = json.loads(DEST.read_text(encoding='utf-8'))
    incoming: list[dict] = []
    successes = 0
    for label, func in SOURCES:
        try:
            items = func()
            incoming.extend(items)
            successes += 1
            print(f'{label}: {len(items)} results')
        except Exception as e:
            print(f'{label} unavailable: {type(e).__name__}: {e}')
    if successes == 0:
        raise SystemExit('No sources available; old data preserved')
    data = merge(data, incoming, datetime.now(timezone.utc).isoformat(timespec='seconds'))
    DEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(data["candidates"])} candidates waiting for review')


if __name__ == '__main__':
    main()
