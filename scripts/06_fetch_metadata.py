"""Step 6: fill in missing description, publisher, date, ISBN, cover and genre tags.

Conservative: never changes title, authors or folders; only fills empty fields; only
accepts a match whose title AND author agree with what's in calibre. Run 05 first so
titles/authors are clean, otherwise most books won't match.

Slow: roughly 10-20 seconds per book. The first run downloads the camoufox browser that
calibre's Amazon source uses ("Warming up camoufox" in the output is normal).
"""
import re
import sys
from threading import Event
sys.path.insert(0, 'scripts')
from common import load_config, open_library
from calibre.utils.logging import ThreadSafeLog
from calibre.ebooks.metadata.sources.identify import identify
from calibre.ebooks.metadata.sources.covers import download_cover

cfg = load_config()
cache = open_library(cfg)
log = ThreadSafeLog(level=ThreadSafeLog.ERROR)
skip = tuple(cfg.get('skip_metadata_folders', []))


def norm(s):
    s = re.sub(r'\(.*?\)|\[.*?\]', ' ', (s or '').lower()).split(':')[0]
    return ' '.join(re.findall(r'[a-z0-9]+', s))


def surnames(authors):
    return {a.split()[-1].lower() for a in authors or [] if a and a.split()}


def good_match(mi, res):
    t1, t2 = norm(mi.title), norm(res.title)
    if not t1 or not t2 or not (t1 in t2 or t2 in t1):
        return False
    return bool(surnames(mi.authors) & surnames(res.authors))


stats = dict(checked=0, matched=0, nomatch=0, covers=0)
for bid in sorted(cache.all_book_ids()):
    folder = cache.field_for('#kfolder', bid) or ''
    if skip and folder.startswith(skip):
        continue
    mi = cache.get_metadata(bid)
    if mi.comments and mi.tags and cache.field_for('cover', bid):
        continue
    stats['checked'] += 1
    try:
        results = identify(log, Event(), title=mi.title, authors=mi.authors,
                           identifiers=mi.identifiers or {}, timeout=30)
    except Exception as e:
        print('ERROR', mi.title, e, flush=True)
        continue
    res = next((r for r in results if good_match(mi, r)), None)
    if res is None:
        stats['nomatch'] += 1
        print('NO MATCH', mi.title, '|', ', '.join(mi.authors), flush=True)
        continue
    stats['matched'] += 1
    changes = {}
    if not mi.comments and res.comments:
        changes['comments'] = res.comments
    if not mi.tags and res.tags:
        changes['tags'] = res.tags
    if not mi.series and res.series:
        changes['series'] = res.series
        changes['series_index'] = res.series_index or 1.0
    if not mi.publisher and res.publisher:
        changes['publisher'] = res.publisher
    if res.pubdate and (not mi.pubdate or mi.pubdate.year <= 101):
        changes['pubdate'] = res.pubdate
    if res.identifiers:
        merged = dict(res.identifiers)
        merged.update(mi.identifiers or {})
        if merged != (mi.identifiers or {}):
            changes['identifiers'] = merged
    for field, val in changes.items():
        cache.set_field(field, {bid: val})
    if not cache.field_for('cover', bid):
        cov = download_cover(log, title=res.title, authors=res.authors,
                             identifiers=res.identifiers or {}, timeout=30)
        if cov:
            cache.set_cover({bid: cov[-1]})
            stats['covers'] += 1
    print('OK', mi.title, '->', ', '.join(sorted(changes)) or 'nothing new', flush=True)
print('SUMMARY', stats)
