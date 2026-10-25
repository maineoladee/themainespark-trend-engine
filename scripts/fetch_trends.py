"""Retrieve headline candidates from public Google News RSS searches.
No API key required; never treats news headlines as verified social-media claims.
"""
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'docs' / 'topics.json'
CATEGORIES = {
    'Economy': 'Nigeria inflation food prices naira exchange rate economy',
    'Politics': 'Nigeria politics INEC 2027 elections governance',
    'Public Services': 'Nigeria electricity education health security jobs',
    'Diaspora': 'Nigerians in UK diaspora remittances immigration',
    'Entertainment': 'Nigeria Nollywood Afrobeats entertainment',
    'International': 'Africa UK US world economy latest',
}

# Broad publisher coverage. Some publishers do not expose a reliable public RSS feed;
# we keep them discoverable using their publisher-constrained Google News RSS search.
PUBLISHERS = {
 'ARISE News':'arise.tv', 'Channels Television':'channelstv.com', 'TVC News':'tvcnews.tv',
 'NTA':'nta.ng', 'AIT':'ait.live', 'News Central':'newscentral.africa',
 'Silverbird':'silverbirdtv.com', 'Plus TV Africa':'plustvafrica.com',
 'Trust TV':'trusttv.com', 'Lagos TV':'lagostelevision.com',
 'Punch':'punchng.com', 'Vanguard':'vanguardngr.com',
 'The Guardian Nigeria':'guardian.ng', 'The Nation':'thenationonlineng.net',
 'Daily Trust':'dailytrust.com', 'Nigerian Tribune':'tribuneonlineng.com',
 'Leadership':'leadership.ng', 'THISDAY':'thisdaylive.com',
 'Daily Independent':'independent.ng', 'Premium Times':'premiumtimesng.com',
 'TheCable':'thecable.ng', 'Sahara Reporters':'saharareporters.com',
 'Peoples Gazette':'gazettengr.com', 'Legit.ng':'legit.ng',
 'Ripples Nigeria':'ripplesnigeria.com', 'BusinessDay':'businessday.ng',
 'Nairametrics':'nairametrics.com', 'Proshare':'proshareng.com',
 'TechCabal':'techcabal.com', 'Techpoint Africa':'techpoint.africa',
 'Pulse Nigeria':'pulse.ng', 'BellaNaija':'bellanaija.com',
 'Complete Sports':'completesports.com', 'Soccernet Nigeria':'soccernet.ng',
 'BBC News':'bbc.com', 'CNN':'cnn.com', 'Al Jazeera':'aljazeera.com',
}
INTERNATIONAL = {'BBC News','CNN','Al Jazeera'}
DIRECT_FEEDS = {
 'ARISE News':'https://www.arise.tv/feed/',
 'Channels Television':'https://www.channelstv.com/feed/',
 'Punch':'https://punchng.com/feed/',
 'Vanguard':'https://www.vanguardngr.com/feed/',
 'Premium Times':'https://www.premiumtimesng.com/feed',
 'TheCable':'https://www.thecable.ng/feed',
 'Nairametrics':'https://nairametrics.com/feed/',
 'BBC News':'https://feeds.bbci.co.uk/news/world/rss.xml',
 'CNN':'http://rss.cnn.com/rss/edition.rss',
 'Al Jazeera':'https://www.aljazeera.com/xml/rss/all.xml',
}

def parse_feed(url, category, publisher, limit=12):
    request = Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; OladayoNewsReader/2.0)'})
    with urlopen(request, timeout=9) as response:
        root = ET.fromstring(response.read(1_500_000))
    items = root.findall('./channel/item')
    if not items: items = root.findall('{http://www.w3.org/2005/Atom}entry')
    for item in items[:limit]:
        title = re.sub(r'\s+', ' ', (item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title') or '').strip())
        link = (item.findtext('link') or '').strip()
        if not link:
            atomlink = item.find('{http://www.w3.org/2005/Atom}link')
            link = atomlink.get('href','') if atomlink is not None else ''
        pub_date = item.findtext('pubDate') or item.findtext('{http://www.w3.org/2005/Atom}updated') or ''
        try: date = parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
        except (ValueError,TypeError,IndexError):
            try: date = datetime.fromisoformat(pub_date.replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
            except (ValueError,TypeError): date = None
        if title and link.startswith('http'):
            yield {'title':title[:240],'url':link,'category':category,'source':publisher,'published_at':date,'publisher':publisher,'origin':'direct RSS'}

def publisher_items(pair):
    publisher, domain = pair
    category = 'International' if publisher in INTERNATIONAL else 'Nigeria'
    url = DIRECT_FEEDS.get(publisher)
    if url:
        try:
            found=list(parse_feed(url,category,publisher))
            if found: return found
        except Exception as exc: print(f'RSS fallback {publisher}: {exc}')
    try:
        return [dict(x, source=publisher,publisher=publisher,origin='Google News site search') for x in get_items(category, f'site:{domain}')][:8]
    except Exception as exc:
        print(f'Publisher unavailable {publisher}: {exc}')
        return []


def get_items(category, term):
    url = 'https://news.google.com/rss/search?q=' + quote(term) + '&hl=en-NG&gl=NG&ceid=NG:en'
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; TheMaineSparkTrendBot/1.0)'})
    with urlopen(request, timeout=18) as response:
        content = response.read(1_500_000)
    root = ET.fromstring(content)
    for item in root.findall('./channel/item')[:35]:
        title = re.sub(r'\s+', ' ', (item.findtext('title') or '').strip())
        link = (item.findtext('link') or '').strip()
        source = (item.findtext('source') or '').strip()
        pub_date = (item.findtext('pubDate') or '').strip()
        if not title or not link:
            continue
        try:
            date = parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
        except (ValueError, TypeError):
            date = None
        yield {'title': title[:240], 'url': link, 'category': category, 'source': source, 'published_at': date, 'origin':'Google News RSS'}

def main():
    existing = []
    if TARGET.exists():
        try:
            existing = json.loads(TARGET.read_text(encoding='utf-8')).get('topics', [])
        except (ValueError, OSError):
            pass
    entries, seen = [], set()
    now = datetime.now(timezone.utc)
    fresh_days = 3
    for category, term in CATEGORIES.items():
        try:
            results = list(get_items(category, term))
            print(f'{category}: {len(results)}')
        except Exception as exc:
            print(f'WARNING {category}: {exc}')
            results = [item for item in existing if item.get('category') == category]
        results.sort(key=lambda i: i.get('published_at') or '', reverse=True)
        fresh = []
        for item in results:
            try:
                age = now - datetime.fromisoformat(item['published_at']) if item.get('published_at') else timedelta(days=999)
            except (ValueError, TypeError):
                age = timedelta(days=999)
            if timedelta(0) <= age <= timedelta(days=fresh_days):
                item['recency'] = 'recent'
                fresh.append(item)
        # Retain older results separately only if no recent headlines were available.
        if not fresh:
            fresh = [dict(item, recency='archive') for item in results[:5]]
        for item in fresh:
            title_key = re.sub(r'[^a-z0-9]+', '', item['title'].casefold())[:140]
            if title_key in seen:
                continue
            seen.add(title_key)
            entries.append(item)
    # Publisher sources are fetched concurrently; the existing category fallback is retained.
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(publisher_items, pair) for pair in PUBLISHERS.items()]
        for future in as_completed(futures):
            for item in future.result():
                try: age = now - datetime.fromisoformat(item['published_at']) if item.get('published_at') else timedelta(days=999)
                except (ValueError,TypeError): age=timedelta(days=999)
                if not timedelta(0)<=age<=timedelta(days=3): continue
                item['recency']='recent'
                title_key=re.sub(r'[^a-z0-9]+','',item['title'].casefold())[:140]
                if title_key in seen: continue
                seen.add(title_key); entries.append(item)
    entries.sort(key=lambda i: (i.get('recency') == 'recent', i.get('published_at') or ''), reverse=True)
    if not entries:
        raise SystemExit('No feeds available and no existing data; not overwriting topics.json')
    TARGET.parent.mkdir(exist_ok=True, parents=True)
    TARGET.write_text(json.dumps({'updated_at': datetime.now(timezone.utc).isoformat(), 'topics': entries}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {len(entries)} topics')

if __name__ == '__main__':
    main()
