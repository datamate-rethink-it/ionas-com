#!/usr/bin/env python3
"""Gemeinsame Helfer fuer die ionas-Migration PHP -> Hugo."""
import json, os, re, shutil, sys

PRJ = os.environ.get('IONAS_PRJ',
                     os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLD = os.path.join(PRJ, '_build')

SRC = os.environ.get('IONAS_SRC')
# Der Referenz-Snapshot des alten PHP-Stands liegt im Repo, damit verify.py
# ohne PHP und ohne den Tarball laeuft.
REF = os.environ.get('IONAS_REF') or os.path.join(BLD, 'reference')

HEAD_MARK = '</header>'
FOOT_MARK = '<footer class="footer-1'


def routes():
    with open(os.path.join(BLD, 'routes.json'), encoding='utf-8') as fh:
        return json.load(fh)


def ref_path(route):
    return os.path.join(REF, 'index.html' if route == 'startseite' else route.lstrip('/') + '/index.html')


def read_ref(route):
    with open(ref_path(route), encoding='utf-8') as fh:
        return fh.read()


def split_page(html):
    """Zerlegt eine gerenderte Seite in Kopf, Rumpf und Fuss."""
    i = html.index(HEAD_MARK) + len(HEAD_MARK)
    j = html.index(FOOT_MARK)
    return html[:i], html[i:j], html[j:]


def write(relpath, text):
    full = os.path.join(PRJ, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return full


def yaml_block(key, value, indent='  '):
    """Mehrzeiligen HTML-Text als YAML-Literal-Block ausgeben."""
    lines = value.split('\n')
    out = [key + ': |-']
    for ln in lines:
        out.append(indent + ln if ln.strip() else '')
    return '\n'.join(out)
