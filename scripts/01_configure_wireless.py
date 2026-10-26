"""Step 1: calibre's wireless device connection for KOReader.

- Start wireless connections automatically when calibre starts
- Use a fixed port (default 9090)
- Prefer EPUB when sending
"""
import sys
sys.path.insert(0, 'scripts')
from common import load_config
from calibre.devices.smart_device_app.driver import SMART_DEVICE_APP as S

AUTOSTART, USE_FIXED_PORT, PORT, USE_METADATA_CACHE = 0, 4, 5, 14

cfg = load_config()
c = S._config()
opts = c.parse()
ec = list(opts.extra_customization or S.EXTRA_CUSTOMIZATION_DEFAULT)
ec += list(S.EXTRA_CUSTOMIZATION_DEFAULT[len(ec):])
ec[AUTOSTART] = True
ec[USE_FIXED_PORT] = True
ec[PORT] = str(cfg.get('wireless_port', 9090))
ec[USE_METADATA_CACHE] = True
c.set('extra_customization', ec)

first = ['epub', 'azw3', 'mobi', 'fb2', 'cbz', 'pdf', 'txt']
fm = first + [f for f in opts.format_map if f not in first]
c.set('format_map', fm)

print('Wireless: autostart on, fixed port', ec[PORT], '| format order:', ', '.join(fm[:5]), '...')
