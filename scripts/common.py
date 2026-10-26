"""Shared helpers. Run every script from the repo root with calibre-debug, e.g.

    calibre-debug -e scripts/04_mirror_folders.py
    calibre-debug -e scripts/04_mirror_folders.py -- --test     (script options go after --)

Close the calibre GUI first: these scripts write to the library directly.
"""
import json
import os
import sys

ROOT = os.getcwd()


def load_config():
    path = os.path.join(ROOT, 'config.json')
    if not os.path.exists(path):
        sys.exit('config.json not found. Copy config.example.json to config.json, edit it, '
                 'and run this script from the repo root.')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def open_library(cfg):
    from calibre.library import db as DB
    return DB(cfg['calibre_library']).new_api


def _escape(s):
    return s.replace("'", "\\'")


def folder_logic(cfg, assign_to=None):
    """Template-language if/elif chain mapping tags to a folder.

    With assign_to=None the chain evaluates to the folder name.
    With assign_to='f' each branch assigns the folder to variable f instead.
    """
    rules = cfg['genre_rules']
    branches = []
    for i, (rx, folder) in enumerate(rules):
        value = "'%s'" % _escape(folder)
        if assign_to:
            value = '%s = %s' % (assign_to, value)
        branches.append("%s '%s' in t then %s" % ('if' if i == 0 else 'elif', _escape(rx), value))
    default = "'%s'" % _escape(cfg['inbox_folder'])
    if assign_to:
        default = '%s = %s' % (assign_to, default)
    return "t = raw_list('tags', ', '); %s else %s fi" % (' '.join(branches), default)


def composite_template(cfg):
    """Shown in the 'KOReader folder' column: manual folder if set, else genre rule."""
    return "program: f = raw_field('#folder', ''); if f then f else %s fi" % folder_logic(cfg)


def send_template(cfg):
    """Path on the device: <folder>/<KOReader filename or 'Title - Author'>.

    raw_field() keeps '/' in folder names; field() would turn them into '_'.
    """
    return ("program: f = raw_field('#folder', ''); if f == '' then %s fi; "
            "n = field('#devname'); if n == '' then n = strcat(field('title'), ' - ', field('authors')) fi; "
            "strcat(f, '/', n)") % folder_logic(cfg, assign_to='f')


def device_path(template, mi, book_id):
    from calibre.library.save_to_disk import get_components
    return '/'.join(get_components(template, mi, book_id, length=250,
                                   sanitize_func=lambda x: x, replace_whitespace=False))
