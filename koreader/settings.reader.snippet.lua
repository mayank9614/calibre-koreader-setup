-- Lines to add inside the `return { ... }` table of koreader/settings.reader.lua
-- Edit the file only while KOReader is CLOSED: it rewrites the file on exit.
-- Back it up first.

    ["calibre_wireless_default_format"] = "epub",
    ["calibre_wireless_url"] = {
        ["address"] = "192.168.1.10",   -- your PC's IP address
        ["port"] = 9090,
    },
    -- Root of your folder structure. Calibre sends books to <this>/<KOReader folder>/...
    ["inbox_dir"] = "/mnt/us/documents/Books",
