"""Step 5: fix junk titles/authors using the Kindle filenames ("Title - Author.epub").

EPUBs from random sources often carry uploader names as the author and site tags in
the title. If your filenames are clean, they are a better source. This script:

- sets the title from the filename (part before the last " - ")
- replaces the authors with the filename's authors only when the stored ones look like
  junk (see JUNK_AUTHOR, or add names to junk_authors in config.json)
- flips "Last, First" author names
- applies per-book fixes from overrides.json (optional, see overrides.example.json)
- sets series for numbered files in a series folder, e.g. ".../Jack Reacher/05 Echo Burning - Lee Child"

Never changes #folder or #devname, so device paths stay the same.
Run with --dry-run first to see what would change.
"""
import json
import os
import re
import sys
sys.path.insert(0, 'scripts')
from common import load_config, open_library

cfg = load_config()
dry = '--dry-run' in sys.argv
cache = open_library(cfg)

junk = ['unknown.*'] + [re.escape(a) for a in cfg.get('junk_authors', [])]
JUNK_AUTHOR = re.compile(r'^(%s)$|z-library|z-lib|\(copy \d+\)' % '|'.join(junk), re.I)

overrides = {}
if os.path.exists('overrides.json'):
    with open('overrides.json', encoding='utf-8') as f:
        overrides = json.load(f)


def clean_authors(authors):
    out = []
    for a in authors:
        parts = a.split(', ')
        if len(parts) > 2 or (len(parts) == 2 and all(' ' in p for p in parts)):
            out.extend(parts)            # "A B, C D, E F" -> three people
        elif len(parts) == 2 and ' ' not in parts[0]:
            out.append(parts[1] + ' ' + parts[0])  # "Last, First"
        else:
            out.append(a)
    return out


skip = tuple(cfg.get('skip_metadata_folders', []))
changed = 0
for bid in sorted(cache.all_book_ids()):
    folder = cache.field_for('#folder', bid) or ''
    dev = cache.field_for('#devname', bid) or ''
    if not dev or (skip and folder.startswith(skip)):
        continue
    old_title, old_authors = cache.field_for('title', bid), list(cache.field_for('authors', bid))
    authors_junk = any(JUNK_AUTHOR.search(a) for a in old_authors)
    series = None
    if dev in overrides:
        o = overrides[dev]
        title = o.get('title', old_title)
        authors = o.get('authors') or clean_authors(old_authors)
        if o.get('series'):
            series = (o['series'], o.get('series_index', 1))
    elif ' - ' in dev:
        title, fa = dev.rsplit(' - ', 1)
        m = re.match(r'^(\d+) (.+)$', title)
        if m and '/' in folder:
            series = (folder.rsplit('/', 1)[1], int(m.group(1)))
            title = m.group(2)
        authors = fa.split(' & ') if authors_junk else clean_authors(old_authors)
    else:
        title, authors = dev, clean_authors(old_authors)

    if title == old_title and authors == old_authors and not series:
        continue
    changed += 1
    print('%-45s | %s%s' % (title[:45], ' & '.join(authors), '  [%s #%s]' % series if series else ''))
    if dry:
        continue
    if title != old_title:
        cache.set_field('title', {bid: title})
    if authors != old_authors:
        cache.set_field('authors', {bid: authors})
    if series and not cache.field_for('series', bid):
        cache.set_field('series', {bid: series[0]})
        cache.set_field('series_index', {bid: float(series[1])})
print('%s %d books' % ('would change' if dry else 'changed', changed))
