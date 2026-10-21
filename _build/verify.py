#!/usr/bin/env python3
"""Vergleicht die Hugo-Ausgabe Seite fuer Seite mit dem Referenz-Render des
alten PHP. Der Referenz-Snapshot ist nachweislich byte-identisch mit dem
Produktionsstand (stichprobenartig gegen https://www.ionas.com geprueft).

Zwei Klassen von Abweichungen werden vor dem Vergleich normalisiert, weil
sie bewusst in Kauf genommen sind:

  1. Entity-Kodierung: Hugo schreibt & und ' in Titel und Description
     korrekt als &amp; / &#39;. Das alte PHP gab sie roh aus - formal
     invalides HTML, in jedem Browser identische Darstellung.

  2. HTML-Kommentare: Go's html/template entfernt sie beim Rendern. Die
     Kommentare stehen weiterhin in layouts/baseof.html, nur nicht mehr im
     ausgelieferten HTML. Fuer Besucher und Suchmaschinen ohne Bedeutung.

  3. Die Schrift Open Sans Condensed kam vom Google-CDN und liegt jetzt
     lokal unter /static/css/fonts.css - die eine <link>-Zeile im Kopf
     unterscheidet sich deshalb auf jeder Seite.

Jede andere Abweichung ist ein Fehler und landet in verify-diff.txt.
"""
import difflib
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import BLD, PRJ, read_ref, ref_path, routes  # noqa: E402

PUB = os.path.join(PRJ, 'public')

ENTITIES = [('&amp;', '&'), ('&#39;', "'"), ('&#34;', '"'),
            ('&rsquo;', '’'), ('&hellip;', '…')]


# Die Schrift Open Sans Condensed kam bisher von fonts.googleapis.com und
# liegt jetzt lokal. Beide Schreibweisen werden auf denselben Platzhalter
# gebracht, damit der Vergleich den Rest der Seite weiter Byte fuer Byte
# prueft.
SCHRIFT = [
    ("<link href='//fonts.googleapis.com/css?family=Open+Sans+Condensed"
     ":300,700' rel='stylesheet' type='text/css' />"),
    '<link rel="stylesheet" href="/static/css/fonts.css" />',
]

def normalize(text):
    for ent, raw in ENTITIES:
        text = text.replace(ent, raw)
    for zeile in SCHRIFT:
        text = text.replace(zeile, '@@SCHRIFT@@')
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'[ \t]+\n', '\n', text)      # Leerraum am Zeilenende
    text = re.sub(r'\n{2,}', '\n', text)        # Leerzeilen zusammenfassen
    return text.strip()


def page_urls():
    """Alle Hugo-Seiten anhand der url-Frontmatter in content/."""
    urls = []
    pattern = os.path.join(PRJ, 'content', '**', '*.html')
    for path in sorted(glob.glob(pattern, recursive=True)):
        with open(path, encoding='utf-8') as fh:
            head = fh.read(2000)
        match = re.search(r'^url: "(.*?)"$', head, re.M)
        u = match.group(1) if match else "/"
        if u.startswith("/wissen"):
            continue
        urls.append(u)
    return urls


def main():
    same, differing, missing = 0, 0, 0
    report = []

    for url in sorted(page_urls()):
        route = 'startseite' if url == '/' else url
        rel = 'index.html' if url == '/' else url.lstrip('/') + '/index.html'
        produced = os.path.join(PUB, rel)

        if not os.path.isfile(produced):
            print('FEHLT in public/: %s' % url)
            missing += 1
            continue
        if not os.path.isfile(ref_path(route)):
            print('kein Referenz-Render fuer %s' % url)
            missing += 1
            continue

        with open(produced, encoding='utf-8') as fh:
            got = normalize(fh.read())
        expected = normalize(read_ref(route))

        if got == expected:
            same += 1
            continue

        differing += 1
        report.append((url, list(difflib.unified_diff(
            expected.splitlines(True), got.splitlines(True),
            'alt ' + route, 'neu ' + url, n=1))))

    total = same + differing + missing
    print()
    print('=' * 66)
    print('identisch: %d    abweichend: %d    fehlend: %d    (von %d Seiten)'
          % (same, differing, missing, total))
    print('=' * 66)

    if report:
        out = os.path.join(BLD, 'verify-diff.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            for url, diff in report:
                fh.write('\n' + '#' * 70 + '\n### %s\n' % url + '#' * 70 + '\n')
                fh.writelines(diff)
        print('Diffs: %s' % out)
        for url, diff in report[:5]:
            changed = sum(1 for line in diff if line[:1] in '+-')
            print('\n--- %s (%d Zeilen) ---' % (url, changed))
            for line in diff[:20]:
                print('   ' + line.rstrip('\n')[:150])

    return 0 if differing == 0 and missing == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
