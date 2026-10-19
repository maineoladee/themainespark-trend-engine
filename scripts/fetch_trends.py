"""Retrieve headline candidates from public Google News RSS searches.
No API key required; never treats news headlines as verified social-media claims.
"""
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
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


def get_items(category, term):
    url = 'https://news.google.com/rss/search?q=' + quote(term) + '&hl=en-NG&gl=NG&ceid=NG:en'
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; TheMaineSparkTrendBot/1.0)'})
    with urlopen(request, timeout=18) as response:
        content = response.read(1_500_000)
    root = ET.fromstring(content)
    for item in root.findall('./channel/item')[:12]:
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
        yield {'title': title[:240], 'url': link, 'category': category, 'source': source, 'published_at': date}

def main():
    existing = []
    if TARGET.exists():
        try:
            existing = json.loads(TARGET.read_text(encoding='utf-8')).get('topics', [])
        except (ValueError, OSError):
            pass
    entries, seen = [], set()
    for category, term in CATEGORIES.items():
        try:
            results = list(get_items(category, term))
            print(f'{category}: {len(results)}')
        except Exception as exc:
            print(f'WARNING {category}: {exc}')
            results = [item for item in existing if item.get('category') == category]
        for item in results:
            title_key = re.sub(r'[^a-z0-9]+', '', item['title'].casefold())[:140]
            if title_key in seen:
                continue
            seen.add(title_key)
            entries.append(item)
    if not entries:
        raise SystemExit('No feeds available and no existing data; not overwriting topics.json')
    TARGET.parent.mkdir(exist_ok=True, parents=True)
    TARGET.write_text(json.dumps({'updated_at': datetime.now(timezone.utc).isoformat(), 'topics': entries}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {len(entries)} topics')

if __name__ == '__main__':
    main()
