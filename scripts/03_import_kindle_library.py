"""Step 3: import the books already on the Kindle, remembering where each one lives.

Walks kindle_books_dir (the Kindle mounted over USB, KOReader closed), adds every EPUB
and records its folder (#folder) and filename (#devname), so sending it back later
lands on exactly the same path and keeps KOReader's reading progress (.sdr sidecars).
"""
import os
import sys
sys.path.insert(0, 'scripts')
from common import load_config, open_library
from calibre.ebooks.metadata.meta import get_metadata

cfg = load_config()
root = cfg['kindle_books_dir']
if not os.path.isdir(root):
    sys.exit('Kindle folder not found: %s (is the Kindle plugged in with KOReader closed?)' % root)
cache = open_library(cfg)

known = {cache.field_for('#folder', b) + '/' + cache.field_for('#devname', b)
         for b in cache.all_book_ids() if cache.field_for('#devname', b)}
added = skipped = failed = 0
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if not d.endswith('.sdr') and not d.startswith('.')]
    for fn in filenames:
        if not fn.lower().endswith('.epub'):
            continue
        rel = os.path.relpath(dirpath, root)
        folder = '' if rel == '.' else rel.replace(os.sep, '/')
        devname = os.path.splitext(fn)[0]
        if folder + '/' + devname in known:
            skipped += 1
            continue
        path = os.path.join(dirpath, fn)
        try:
            with open(path, 'rb') as f:
                mi = get_metadata(f, 'epub')
            ids, _ = cache.add_books([(mi, {'EPUB': path})], add_duplicates=True)
            cache.set_field('#folder', {ids[0]: folder})
            cache.set_field('#devname', {ids[0]: devname})
            added += 1
        except Exception as e:
            failed += 1
            print('FAILED', path, e)
print('added %d, already imported %d, failed %d' % (added, skipped, failed))
