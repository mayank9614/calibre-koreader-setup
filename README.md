# Calibre + KOReader: genre folders, wireless, and a nicer Kindle

A step-by-step setup for managing a KOReader library (on a jailbroken Kindle, but it works for
any KOReader device) from **calibre on Windows**:

- **Your KOReader folder structure is visible and editable in calibre.**
- **New books go to the right folder automatically, based on genre.**
- Books are sent **over Wi‑Fi**, not USB.
- You can browse your calibre library **from the Kindle** (OPDS).
- Titles, authors, series and descriptions get cleaned up.
- The Kindle gets a nicer home screen with the **SimpleUI** and **Bookshelf** plugins.

```
New EPUB ─► calibre ─► download metadata ─► genre tags ─► "KOReader folder" column
                                                              │ (override by hand if needed)
                                                              ▼
                                   Send to device (Wi‑Fi) ─► /Books/<folder>/<Title - Author>.epub
```

Tested with **calibre 9.17**, **KOReader v2026.07.1**, and a **Kindle 10th generation (2019)**.

---

## The folder scheme

Books live under one root on the device, `/mnt/us/documents/Books`, in numbered genre folders:

```
Books/
├── 0 Inbox                          ← anything the rules can't place
├── 1 Fiction - Thrillers & Mystery/
│   └── Jack Reacher/                ← subfolders work too
├── 2 Fiction - Literary & Classics/
├── 3 Sci-Fi & Fantasy/
├── 4 History & Politics/
├── 5 Ideas, Money & Mind/
├── 6 Tech & Programming/
├── 7 Magazines & News/
└── 8 Misc/
```

Use your own folder names. Just keep them in sync with `genre_rules` in `config.json`.

## How it works

Calibre gets three custom columns:

| Column | Lookup name | What it holds |
|---|---|---|
| **KOReader folder** | `#kfolder` | Computed. The manual folder if one is set, otherwise a folder picked from the book's **genre tags**. |
| KOReader folder (manual) | `#folder` | Type a folder here to override the genre rule. Imported books get their current folder. |
| KOReader filename | `#devname` | The book's filename on the device. Keeping it means reading progress and highlights (`.sdr` folders) stay attached. |

The wireless **send template** uses the same logic, so a book lands exactly where the
**KOReader folder** column says:

```
<KOReader folder>/<KOReader filename, or "Title - Author">.epub
```

### Genre rules

The first rule that matches any tag wins. Here are the defaults from `config.example.json`:

| Tags containing… | Folder |
|---|---|
| science fiction, fantasy, dystopia | 3 Sci-Fi & Fantasy |
| thriller, mystery, crime, detective | 1 Fiction - Thrillers & Mystery |
| programming, computer, software, algorithm | 6 Tech & Programming |
| fiction (not *non*fiction), novel, classic, poetry | 2 Fiction - Literary & Classics |
| science (not *political* science), philosophy, psychology, economics, business, self-help | 5 Ideas, Money & Mind |
| history, politics, biography, memoir, war | 4 History & Politics |
| *(nothing matched)* | 0 Inbox |

**Why this order:** philosophy and science come before history, so *The Physicist and the
Philosopher* (tagged Philosophy + History) goes to Ideas. "Juvenile Nonfiction" won't match
`fiction`.

---

## Requirements

- **Windows** with **[calibre](https://calibre-ebook.com/)** installed (`C:\Program Files\Calibre2`).
- **KOReader** on your e‑reader. On a Kindle, this needs a jailbreak; see the
  [KOReader wiki](https://github.com/koreader/koreader/wiki/Installation-on-Kindle-devices).
- The PC and the e‑reader on the **same Wi‑Fi network**.
- **USB** for the one-time import and for installing plugins. On a Kindle, the USB drive
  only appears when **KOReader is closed**.

## Setup

> All scripts run with calibre's own Python: `calibre-debug`.
> **Close calibre first:** the scripts write to the library directly. Run them from this repo's folder.
> **Back up your library** first by copying `metadata.db` from your calibre library folder.

```powershell
git clone https://github.com/mayank9614/calibre-koreader-setup
cd calibre-koreader-setup
copy config.example.json config.json   # then edit it
calibre --shutdown-running-calibre
```

Put `C:\Program Files\Calibre2` on your PATH, or call `"C:\Program Files\Calibre2\calibre-debug.exe"` directly.

### Step 1: Wireless connection in calibre

```powershell
calibre-debug -e scripts/01_configure_wireless.py
```

This turns on **Start wireless device connection** at startup, fixes it to port **9090**, and
makes **EPUB** the first format to send. You can do the same by hand: *Connect/share → Start
wireless device connection → options*.

When calibre starts, allow it through **Windows Firewall** if asked.

### Step 2: KOReader settings

On the device, in KOReader, go to **Tools → Calibre → Wireless settings**:

- **Server address:** your PC's IP address and port **9090**. Find the IP with `ipconfig`.
- **Inbox folder:** the **root** of your folder structure (`/mnt/us/documents/Books`), not a
  subfolder. Calibre creates the genre folders under it.

You can also edit `koreader/settings.reader.lua` directly. See
[`koreader/settings.reader.snippet.lua`](koreader/settings.reader.snippet.lua). Only do this
while KOReader is closed, because it rewrites the file when it exits.

**Test it:** in KOReader, go to **Tools → Calibre → Connect**. Calibre should show a **Device** button.

### Step 3: Add the folder columns

```powershell
calibre-debug -e scripts/02_add_columns.py
```

### Step 4: Import the books already on your device (optional)

Plug the device in over USB with KOReader closed, and set `kindle_books_dir` in `config.json`
(for example `D:/documents/Books`).

```powershell
calibre-debug -e scripts/03_import_kindle_library.py
```

Every EPUB is added with its current folder and filename recorded. You can safely run it again:
books already imported are skipped.

### Step 5: Mirror the folders when sending

```powershell
calibre-debug -e scripts/04_mirror_folders.py -- --test   # preview where sample genres go
calibre-debug -e scripts/04_mirror_folders.py
```

This sets the send template and adds **one virtual library per folder** (the button at the top
left of calibre). It puts the **KOReader folder** column next to the title. Then it **checks**
that every imported book maps back to its current path. You want
`existing books whose device path would change: 0`.

### Step 6: Clean up titles and authors (optional)

EPUBs often carry junk metadata: uploader names as the author, and download-site tags in the
title. If your **filenames** are clean (`Title - Author.epub`), use them:

```powershell
calibre-debug -e scripts/05_clean_titles.py -- --dry-run
calibre-debug -e scripts/05_clean_titles.py
```

- Add known junk author names to `junk_authors` in `config.json`.
- For filenames that don't split cleanly, or need series info, add entries to
  `overrides.json` (see [`overrides.example.json`](overrides.example.json)).
- Numbered files in a subfolder (`Jack Reacher/05 Echo Burning - Lee Child`) get a series
  automatically.

### Step 7: Download descriptions, covers and genre tags

```powershell
calibre-debug -e scripts/06_fetch_metadata.py
```

- It only fills **empty** fields, and only accepts a match when both **title and author agree**.
- It's slow: about 10–20 seconds per book. Run it in the background.
- The first run downloads the **camoufox** browser that calibre's Amazon source now uses. Output
  like `Warming up camoufox on: https://www.amazon.com/...` is normal: it uses a fresh browser
  profile, not your logins.

### Step 8: Browse your library from the device (OPDS)

1. In calibre, go to **Preferences → Sharing over the net**. Tick **Run server automatically when
   calibre starts** and keep port **8080**. Consider ticking **Require username and password**.
2. In KOReader, open the **file browser** (not a book). Go to **Search (🔍) → OPDS catalog**, then
   tap **☰ / +** at the top left and choose **Add catalog**.
3. Enter the URL `http://<your-PC-IP>:8080/opds`.

If **OPDS catalog** isn't in the menu, enable it under **Tools → More tools → Plugin management**.

Books downloaded through OPDS go to KOReader's download folder. Use **Send to device** for books
you want filed into genre folders.

### Step 9: A nicer home screen (SimpleUI + Bookshelf)

| Plugin | What it does |
|---|---|
| [SimpleUI](https://github.com/doctorhetfield-cmd/simpleui.koplugin) | Home screen, bottom tab bar, status bar, reading streaks, quick settings |
| [Bookshelf](https://github.com/AndyHazz/bookshelf.koplugin) | Your library as covers on shelves, grouped by folder, series, author or genre |

Both need **KOReader 2026.03 or newer** (Help → Version) and the built-in **Cover browser**
plugin enabled.

1. Download **`*.koplugin.zip` from each project's Releases page**, not the green *Code* button.
2. Unzip each one. You should get a folder named `simpleui.koplugin` or `bookshelf.koplugin`
   containing `main.lua`.
3. With KOReader closed and the Kindle on USB, copy both folders into **`koreader/plugins/`**.
4. Eject the Kindle and open KOReader. Finish SimpleUI's welcome screen.
5. Optionally, set **Start with → bookshelf** in the file browser menu.

They run fine together: SimpleUI only auto-disables ZenOS, Burrow, QuickUI and Reader Menu
Redesign. Both plugins have built-in updaters.

**If something breaks:** go to Tools → More tools → Plugin management and untick the plugin, or
delete its folder from `koreader/plugins` over USB.

---

## Day to day: adding a new book

**In calibre:**
1. Drag the EPUB into calibre.
2. Right‑click it and choose **Edit metadata → Download metadata**. This adds genre tags.
3. Check the **KOReader folder** column. If it's wrong, type the right folder into
   **KOReader folder (manual)**, or a new one like `5 Ideas, Money & Mind/Time`.
4. In KOReader, go to **Tools → Calibre → Connect**. In calibre, choose **Send to device**.

**Or for a whole folder of new books** (close calibre first):

```powershell
calibre-debug -e scripts/07_add_new_books.py -- "C:/Users/YOU/Downloads/Books"
```

It prints the folder each book got. Reopen calibre, fix any folders, then send.

**To move a book to another folder later:** change its **KOReader folder (manual)** and send it
again. With *Replace books with same calibre ID* on (the default), calibre removes the old copy.
This only works for books calibre has already sent at least once. After importing, select all
books and send them once to register them.

---

## Gotchas learned the hard way

- **`raw_field()`, not `field()`, in path templates.** `field()` turns `/` in a value into `_`,
  which flattens `1 Fiction/Jack Reacher` into `1 Fiction_Jack Reacher`.
- **Close calibre before running the scripts.** Running scripts while the GUI is open risks
  corrupting the library. Calibre's content server refuses remote writes (`Forbidden`), so you
  can't work around this through the server.
- **Edit `settings.reader.lua` only while KOReader is closed.** It overwrites the file on exit.
- **The Kindle's USB drive only appears with KOReader closed.**
- **Point KOReader's inbox at the root folder.** Calibre's template creates the subfolders.
- **Keep the filenames** (`#devname`) when re-sending existing books. Renaming a file orphans
  its `.sdr` folder, which holds reading progress and highlights.
- **Make sure the "nonfiction" rule comes before "fiction".**
- **Don't set calibre's IP to one that changes.** Reserve your PC's IP in your router, or
  update KOReader's wireless settings when it changes.

## Undo

- **Calibre:** restore your backed-up `metadata.db`, or delete the three columns under
  Preferences → Add your own columns. Wireless settings are under *Connect/share*.
- **KOReader:** restore your backed-up `settings.reader.lua` (with KOReader closed), and delete
  the plugin folders from `koreader/plugins`.

## License

MIT. See [LICENSE](LICENSE). SimpleUI and Bookshelf are separate projects with their own
licenses (GPL-3.0 and AGPL-3.0).
