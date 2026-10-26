"""Step 2: the three custom columns that make the folder mirroring work.

  #folder   KOReader folder (manual)  - type a folder here to override the genre rule
  #devname  KOReader filename         - original filename on the device, without extension
  #kfolder  KOReader folder           - computed: #folder if set, otherwise from genre tags
"""
import sys
sys.path.insert(0, 'scripts')
from common import load_config, open_library, composite_template

cfg = load_config()
cache = open_library(cfg)
existing = cache.field_metadata.custom_field_keys()

for label, name in (('folder', 'KOReader folder (manual)'), ('devname', 'KOReader filename')):
    if '#' + label not in existing:
        cache.create_custom_column(label, name, 'text', False)
        print('created #%s' % label)

display = {'composite_template': composite_template(cfg), 'composite_sort': 'text',
           'make_category': True, 'contains_html': False, 'use_decorations': False}
if '#kfolder' not in existing:
    cache.create_custom_column('kfolder', 'KOReader folder', 'composite', False, display=display)
    print('created #kfolder')
else:
    num = cache.field_metadata['#kfolder']['colnum']
    cache.backend.set_custom_column_metadata(num, display=display)
    print('updated #kfolder genre rules')
