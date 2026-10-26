"""Day-to-day: add new EPUBs from a folder and see which KOReader folder each one gets.

    calibre-debug -e scripts/07_add_new_books.py -- "C:/Users/YOU/Downloads/Books"

For each EPUB:
- title/author from the file's metadata; if that looks like junk, from a filename like
  "Title (Author) (anything).epub" or "Title - Author.epub"
- looks the book up online for description and genre tags
- the genre tags pick the KOReader folder (config.json -> genre_rules)
Then review the KOReader folder column in calibre, override any in
"KOReader folder (manual)", and Send to device.
"""
import os
import re
import sys
from threading import Event
sys.path.insert(0, 'scripts')
from common import load_config, open_library
from calibre.utils.logging import ThreadSafeLog
from calibre.ebooks.metadata.meta import get_metadata
from calibre.ebooks.metadata.sources.identify import identify

if len(sys.argv) < 2 or not os.path.isdir(sys.argv[-1]):
    sys.exit('usage: calibre-debug -e scripts/07_add_new_books.py -- <folder with epubs>')
src = sys.argv[-1]
cfg = load_config()
cache = open_library(cfg)
log = ThreadSafeLog(level=ThreadSafeLog.ERROR)
JUNK = re.compile(r'^unknown|z-lib|[0-9A-F]{32}|^$', re.I)


def from_filename(fn):
    stem = os.path.splitext(fn)[0]
    m = re.match(r'^(.+?) \(([^()]+)\)', stem)
    if m:
        return m.group(1).strip(), [a.strip() for a in re.split(r',|&| and ', m.group(2)) if a.strip()]
    if ' - ' in stem:
        t, a = stem.rsplit(' - ', 1)
        return t.strip(), [x.strip() for x in a.split('&')]
    return stem, []


existing = {cache.field_for('title', b).lower() for b in cache.all_book_ids()}
for fn in sorted(os.listdir(src)):
    if not fn.lower().endswith('.epub'):
        continue
    path = os.path.join(src, fn)
    with open(path, 'rb') as f:
        mi = get_metadata(f, 'epub')
    if JUNK.search(mi.title or '') or any(JUNK.search(a) for a in mi.authors):
        t, a = from_filename(fn)
        mi.title = t
        if a:
            mi.authors = a
    if mi.title.lower() in existing:
        print('SKIP already in library:', mi.title)
        continue
    try:
        res = identify(log, Event(), title=mi.title, authors=mi.authors, timeout=30)
    except Exception:
        res = []
    if res:
        r = res[0]
        mi.tags = r.tags or mi.tags
        mi.comments = mi.comments or r.comments
        mi.publisher = mi.publisher or r.publisher
        mi.identifiers = dict(r.identifiers or {}, **(mi.identifiers or {}))
    ids, _ = cache.add_books([(mi, {'EPUB': path})])
    bid = ids[0]
    cache.set_field('#devname', {bid: '%s - %s' % (mi.title, ' & '.join(mi.authors))})
    print('ADDED %-40s -> %s   (tags: %s)' % (mi.title[:40], cache.field_for('#kfolder', bid), ', '.join(mi.tags or [])))
