#!/usr/bin/env python3
"""Vergleicht die erzeugten Wissensseiten mit dem Stand der WordPress-
Installation (_build/reference-wissen/, am 21.10.2026 live abgerufen).

Anders als beim PHP-Teil ist hier kein byte-identisches Ergebnis das Ziel:
der WordPress-Kopf enthielt Emoji-Skripte, oEmbed- und wp-json-Verweise,
XML-RPC-Pingback und Gutenberg-CSS, die bewusst nicht mitgekommen sind.
Geprueft wird deshalb, was fuer Besucher und Suchmaschinen zaehlt:

  * der Artikeltext Zeichen fuer Zeichen
  * Titel, Description, Canonical und Robots-Angabe
  * die uebernommenen Kommentare (Anzahl und Zuordnung)
  * Vor-/Zurueck-Verweise und Schlagwort-Verweise
  * die Teaser auf der Uebersichtsseite

Normalisiert werden zwei bekannte Abweichungen:
  * Hugo schreibt " als &#34; und + als &#43;, Yoast schrieb &quot;
    bzw. +. Gleiche Bedeutung, gleiche Darstellung; im <title> laesst
    sich Gos Maskierung nicht abschalten.
  * Hugo ersetzt den <!--more-->-Trenner intern durch Zeilenumbrueche;
    zwischen Blockelementen ist das ohne Wirkung.
"""
import difflib
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import BLD, PRJ  # noqa: E402

PUB = os.path.join(PRJ, 'public')
REFW = os.environ.get('IONAS_REFW') or os.path.join(BLD, 'reference-wissen')

KOPF_FELDER = [
    ('title', r'<title>(.*?)</title>'),
    ('description', r'<meta name="description" content="(.*?)" />'),
    ('canonical', r'<link rel="canonical" href="(.*?)" />'),
    ('robots', r"<meta name='robots' content='(.*?)' />"),
]


def norm(text):
    text = text.replace('&#34;', '&quot;').replace('&#39;', '&#039;')
    text = text.replace('&#43;', '+')
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text


def entry(html):
    i = html.index('<div class="entry">')
    j = html.index('<hr>\n        </div>', i)
    return html[i:j]


def lies(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def teaser_map(html):
    """slug -> Teaser-HTML einer Uebersichtsseite."""
    i = html.index('<section class="content-10 blog"')
    j = html.index('<div class="col-sm-3">', i)
    out = {}
    for block in re.split(r'(?=<h2><a href=)', html[i:j])[1:]:
        m = re.search(r'href="https://www\.ionas\.com/wissen/([^/#"]+)/"', block)
        e = re.search(r'<div class="entry">\s*(.*?)\s*<hr>\s*</div>', block, re.S)
        if m and e:
            out[m.group(1)] = e.group(1)
    return out


def main():
    slugs = sorted(os.path.basename(os.path.dirname(p)) for p in
                   glob.glob(os.path.join(REFW, 'wissen', '*', 'index.html')))
    fehler = []
    gleich_text = 0
    kopf_ok = {name: 0 for name, _ in KOPF_FELDER}
    kommentare_ok = nav_ok = tags_ok = 0
    n_kommentare = 0

    for slug in slugs:
        neu_pfad = os.path.join(PUB, 'wissen', slug, 'index.html')
        if not os.path.isfile(neu_pfad):
            fehler.append((slug, 'Seite fehlt in public/'))
            continue
        neu, alt = lies(neu_pfad), lies(os.path.join(REFW, 'wissen', slug, 'index.html'))

        # --- Artikeltext
        a, b = norm(entry(neu)), norm(entry(alt))
        if a == b:
            gleich_text += 1
        else:
            d = [x for x in difflib.unified_diff(b.splitlines(True), a.splitlines(True),
                                                 n=0) if x[:1] in '+-']
            fehler.append((slug, 'Artikeltext weicht ab (%d Zeilen)' % len(d)))

        # --- Kopf
        for name, pat in KOPF_FELDER:
            ma, mb = re.search(pat, neu, re.S), re.search(pat, alt, re.S)
            if ma and mb and norm(ma.group(1)) == norm(mb.group(1)):
                kopf_ok[name] += 1
            elif mb is None and ma is None:
                kopf_ok[name] += 1
            else:
                fehler.append((slug, '%s: alt=%r neu=%r' % (
                    name, mb.group(1)[:60] if mb else None,
                    ma.group(1)[:60] if ma else None)))

        # --- Kommentare
        ids_alt = set(re.findall(r'<div class="comment" id="comment-(\d+)"', alt))
        ids_neu = set(re.findall(r'<div class="comment" id="comment-(\d+)"', neu))
        if ids_alt == ids_neu:
            kommentare_ok += 1
            n_kommentare += len(ids_alt)
        else:
            fehler.append((slug, 'Kommentare: alt %d, neu %d (fehlen: %s)' % (
                len(ids_alt), len(ids_neu), sorted(ids_alt - ids_neu)[:5])))

        # --- Vor/Zurueck
        def nav(s):
            return [(m.group(1), m.group(2)) for m in
                    re.finditer(r'<a href="([^"]+)" rel="(prev|next)">', s)]
        if nav(neu) == nav(alt):
            nav_ok += 1
        else:
            fehler.append((slug, 'Vor/Zurueck: alt=%s neu=%s' % (nav(alt), nav(neu))))

        # --- Schlagwort-Verweise im Kopfbereich des Artikels
        def tags(s):
            m = re.search(r'<div id="meta">(.*?)</div>', s, re.S)
            return re.findall(r'href="(?:https://www\.ionas\.com)?/wissen/tag/([^"/]+)/"',
                              m.group(1) if m else '')
        if tags(neu) == tags(alt):
            tags_ok += 1
        else:
            fehler.append((slug, 'Schlagwörter: alt=%s neu=%s' % (tags(alt), tags(neu))))

    # --- Uebersichtsseiten
    teaser_fehler = 0
    alt_t, neu_t = {}, {}
    for ref, pub in ((os.path.join(REFW, 'wissen', 'index.html'),
                      os.path.join(PUB, 'wissen', 'index.html')),
                     (os.path.join(REFW, 'wissen', 'page', '2', 'index.html'),
                      os.path.join(PUB, 'wissen', 'page', '2', 'index.html'))):
        if not (os.path.isfile(ref) and os.path.isfile(pub)):
            fehler.append(('uebersicht', 'Seite fehlt: %s' % pub))
            continue
        alt_t.update(teaser_map(lies(ref)))
        neu_t.update(teaser_map(lies(pub)))
    for slug, t in sorted(alt_t.items()):
        if slug not in neu_t:
            fehler.append(('uebersicht', 'Teaser fehlt: %s' % slug))
            teaser_fehler += 1
        elif norm(t) != norm(neu_t[slug]):
            teaser_fehler += 1
            fehler.append(('uebersicht', 'Teaser weicht ab: %s' % slug))

    n = len(slugs)
    print('=' * 70)
    print('Wissensartikel geprüft: %d' % n)
    print('  Artikeltext identisch        %3d / %d' % (gleich_text, n))
    for name, _ in KOPF_FELDER:
        print('  %-27s %3d / %d' % (name, kopf_ok[name], n))
    print('  Kommentare vollständig       %3d / %d  (%d Kommentare)'
          % (kommentare_ok, n, n_kommentare))
    print('  Vor/Zurück-Verweise          %3d / %d' % (nav_ok, n))
    print('  Schlagwort-Verweise          %3d / %d' % (tags_ok, n))
    print('  Teaser der Übersicht         %3d / %d' % (len(alt_t) - teaser_fehler,
                                                       len(alt_t)))
    print('=' * 70)
    if fehler:
        out = os.path.join(BLD, 'verify-wissen.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            for slug, msg in fehler:
                fh.write('%s: %s\n' % (slug, msg))
        print('%d Abweichungen, Liste in %s' % (len(fehler), out))
        for slug, msg in fehler[:12]:
            print('  %-46s %s' % (slug[:46], msg[:110]))
    else:
        print('keine Abweichungen')
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
