"""Step 4: make "Send to device" mirror the KOReader folder structure.

- Wireless send template: <KOReader folder>/<KOReader filename>.epub
- One virtual library per top-level folder
- Book list shows the KOReader folder column next to the title
- Verifies every imported book maps back to its current path on the Kindle

Pass --test to only print where a few sample genres would go.
"""
import sys
sys.path.insert(0, 'scripts')
from common import load_config, open_library, send_template, device_path
from calibre.devices.smart_device_app.driver import SMART_DEVICE_APP as S
from calibre.ebooks.metadata.book.base import Metadata

cfg = load_config()
template = send_template(cfg)

if '--test' in sys.argv:
    cache = open_library(cfg)
    for tags in (['Fiction', 'Literary'], ['Science Fiction'], ['Philosophy'], ['History'],
                 ['Mystery'], ['Computers'], ['Juvenile Nonfiction', 'Technology'], []):
        mi = Metadata('Sample Book', ['Some Author'])
        mi.tags = tags
        mi.set_all_user_metadata(cache.field_metadata.custom_field_metadata())
        print('%-40s -> %s' % (tags, device_path(template, mi, 0)))
    sys.exit()

S._config().set('save_template', template)
print('send template set')

cache = open_library(cfg)
folders = {v for v in cache.all_field_for('#kfolder', cache.all_book_ids()).values() if v}
tops = sorted({f.split('/')[0] for f in folders} | {r[1] for r in cfg['genre_rules']} | {cfg['inbox_folder']})
vls = dict(cache.pref('virtual_libraries', {}))
for t in tops:
    vls[t] = '#kfolder:"~^%s(/|$)"' % t.replace('(', r'\(').replace(')', r'\)')
cache.set_pref('virtual_libraries', vls)
print('virtual libraries:', ', '.join(tops))

order = ['ondevice', 'title', '#kfolder', 'authors', 'series', 'rating', 'tags', 'size', 'timestamp',
         'publisher', 'pubdate', '#folder', '#devname', 'last_modified', 'languages', 'formats', 'id', 'path']
cache.set_pref('books view state', {
    'hidden_columns': ['#folder', '#devname', 'last_modified', 'languages', 'formats', 'id', 'path',
                       'publisher', 'pubdate'],
    'column_positions': {name: i for i, name in enumerate(order)},
    'column_sizes': {'title': 260, '#kfolder': 260, 'authors': 180},
    'sort_history': [['#kfolder', True], ['title', True]],
    'column_alignment': {},
})

bad = 0
for bid in cache.all_book_ids():
    mi = cache.get_metadata(bid)
    if not mi.get('#devname') or not mi.get('#folder'):
        continue
    want = mi.get('#folder') + '/' + mi.get('#devname')
    got = device_path(template, mi, bid)
    if got != want:
        bad += 1
        print('MISMATCH', want, '->', got)
print('existing books whose device path would change:', bad)
