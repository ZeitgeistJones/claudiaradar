#!/usr/bin/env python3
"""Daily public-source discovery for Claudia Radar, no dependencies."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import hashlib, json, re, xml.etree.ElementTree as ET

DEST = Path(__file__).resolve().parents[1] / 'dist' / 'data' / 'mentions.json'
TERMS = ['"claudia.gallery"', '"Claudia" "anabology"', '"claudia_popstar"']

def fetch(url):
    req = Request(url, headers={'User-Agent':'ClaudiaRadar/1.0 (research bot)', 'Accept':'*/*'})
    with urlopen(req, timeout=16) as res: return res.read(2000000)

def relevant(title, description=''):
    text = re.sub('<[^>]*>',' ', f'{title} {description}').lower()
    return ('claudia' in text and any(x in text for x in ('anabology','slopcore','ai popstar','ai pop star','claude music video'))) or any(x in text for x in ('claudia.gallery','claudia_popstar','claudiathepopstar'))

def canonical(url):
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),'',''))

def record(title,url,day,outlet,category):
    ident=hashlib.sha256(canonical(url).encode()).hexdigest()[:16]
    return dict(id='candidate-'+ident,title=title[:180],url=url,date=day,outlet=outlet[:80],category=category,tier='Unclassified',origin='Unclassified',verification='Needs review',notes='Automatically discovered. Confirm identity, publisher, date and uniqueness before counting.')

def news():
    found=[]
    for term in TERMS:
        url='https://news.google.com/rss/search?'+urlencode({'q':term,'hl':'en-US','gl':'US','ceid':'US:en'})
        root=ET.fromstring(fetch(url))
        for item in root.findall('.//item'):
            title=item.findtext('title','').strip()
            link=item.findtext('link','').strip()
            if not link.startswith('http') or not relevant(title,item.findtext('description','')):continue
            try:day=parsedate_to_datetime(item.findtext('pubDate','')).date().isoformat()
            except (ValueError,TypeError):day=datetime.now(timezone.utc).date().isoformat()
            found.append(record(title,link,day,item.findtext('source','') or 'Google News','News'))
    return found

def hacker_news():
    url='https://hn.algolia.com/api/v1/search_by_date?'+urlencode({'query':'claudia.gallery','tags':'story,comment','hitsPerPage':100})
    hits=json.loads(fetch(url)).get('hits',[])
    found=[]
    for hit in hits:
        title=hit.get('title') or hit.get('story_title') or 'Hacker News comment about Claudia'
        if not relevant(title,hit.get('comment_text') or ''):continue
        obj=hit.get('objectID');day=str(hit.get('created_at',''))[:10]
        if not obj or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):continue
        found.append(record(title,'https://news.ycombinator.com/item?id='+str(obj),day,'Hacker News','Forums'))
    return found

def merge(data,new,now):
    seen={canonical(x['url']) for x in data.get('verified',[]) if x.get('url')}
    candidates=[]
    for x in new+data.get('candidates',[]):
        url=x.get('url','')
        if not url.startswith(('https://','http://')) or canonical(url) in seen:continue
        seen.add(canonical(url))
        x.update(verification='Needs review',tier='Unclassified',origin='Unclassified')
        candidates.append(x)
    data['candidates']=sorted(candidates,key=lambda x:x.get('date',''),reverse=True)[:150]
    data['updatedAt']=now
    return data

def main():
    data=json.loads(DEST.read_text(encoding='utf-8'))
    incoming=[];successes=0
    for label,func in [('Google News',news),('Hacker News',hacker_news)]:
        try:
            items=func();incoming.extend(items);successes+=1
            print(f'{label}: {len(items)} results')
        except Exception as e:print(f'{label} unavailable: {type(e).__name__}: {e}')
    if successes==0:raise SystemExit('No sources available; old data preserved')
    data=merge(data,incoming,datetime.now(timezone.utc).isoformat(timespec='seconds'))
    DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(data["candidates"])} candidates waiting for review')

if __name__=='__main__':main()
