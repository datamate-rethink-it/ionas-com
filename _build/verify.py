#!/usr/bin/env python3
"""Prueft, dass die 96 Seiten des alten PHP-Teils unveraendert geblieben sind.

Verglichen wird gegen _build/reference/ - die Routen des alten
switch-Routers, gerendert und stichprobenartig gegen die damalige Live-Seite
geprueft.

Verglichen wird der **Seitenrumpf**, also alles zwischen </header> und
<footer>: die eigentlichen Texte der Leistungs-, Staedte- und
Hilfethemenseiten. Diese Inhalte sind eingefroren - die Hotline ist seit dem
01.04.2020 eingestellt, an "PC Hilfe Wuppertal" schreibt niemand mehr. Jede
Abweichung dort ist ein Fehler, keine Absicht.

Kopf und Fussleiste sind **nicht** Teil des Vergleichs. Sie sind geteilte
Bestandteile, die bewusst weiterentwickelt werden - seit dem Umzug die lokal
ausgelieferte Schrift, der Wegfall von Google+ und Alexa, das reparierte
og:image. Jede dieser Verbesserungen haette sonst einen Eintrag in einer
Ausnahmeliste gebraucht, bis "identisch" nichts mehr bedeutet.

Aus dem Kopf geprueft werden stattdessen die drei Angaben, die der alte
Router pro Route gesetzt hat und die sich nicht aendern duerfen: Titel,
Description und Canonical.

Zwei Abweichungen werden normalisiert:
  * Entity-Kodierung: Hugo schreibt & und ' korrekt als &amp; / &#39;, das
    alte PHP gab sie roh aus. Gleiche Darstellung in jedem Browser.
  * HTML-Kommentare: Go's html/template entfernt sie beim Rendern. Sie
    stehen weiterhin in den Layouts, nur nicht mehr im Ergebnis.
"""
import difflib
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import BLD, PRJ, read_ref, ref_path  # noqa: E402

PUB = os.path.join(PRJ, 'public')

ENTITIES = [('&amp;', '&'), ('&#39;', "'"), ('&#34;', '"'), ('&#43;', '+'),
            ('&rsquo;', '’'), ('&hellip;', '…')]

KOPF_FELDER = [
    ('Titel', r'<title>(.*?)</title>'),
    ('Description', r'<meta name="description" content=\'(.*?)\' />'),
    ('Canonical', r'<link rel="canonical" href="(.*?)" />'),
]

RUMPF_START = '</header>'
RUMPF_ENDE = '<footer class="footer-1'


def normalize(text):
    for ent, raw in ENTITIES:
        text = text.replace(ent, raw)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def rumpf(html):
    i = html.index(RUMPF_START) + len(RUMPF_START)
    j = html.index(RUMPF_ENDE)
    return html[i:j]


def page_urls():
    """Alle Seiten des PHP-Teils anhand der url-Frontmatter in content/."""
    urls = []
    pattern = os.path.join(PRJ, 'content', '**', '*.html')
    for path in sorted(glob.glob(pattern, recursive=True)):
        with open(path, encoding='utf-8') as fh:
            head = fh.read(2000)
        match = re.search(r'^url: "(.*?)"$', head, re.M)
        u = match.group(1) if match else '/'
        if u.startswith('/wissen'):
            continue
        urls.append(u)
    return urls


def main():
    gleich, abweichend, fehlend, kopf_ok = 0, 0, 0, 0
    report = []

    for url in sorted(page_urls()):
        route = 'startseite' if url == '/' else url
        rel = 'index.html' if url == '/' else url.lstrip('/') + '/index.html'
        erzeugt = os.path.join(PUB, rel)

        if not os.path.isfile(erzeugt):
            print('FEHLT in public/: %s' % url)
            fehlend += 1
            continue
        if not os.path.isfile(ref_path(route)):
            print('kein Referenz-Render fuer %s' % url)
            fehlend += 1
            continue

        with open(erzeugt, encoding='utf-8') as fh:
            neu_roh = fh.read()
        alt_roh = read_ref(route)

        neu, alt = normalize(rumpf(neu_roh)), normalize(rumpf(alt_roh))
        if neu == alt:
            gleich += 1
        else:
            abweichend += 1
            report.append((url, list(difflib.unified_diff(
                alt.splitlines(True), neu.splitlines(True),
                'alt ' + route, 'neu ' + url, n=1))))

        # Titel, Description und Canonical stammen aus dem alten Router und
        # duerfen sich nicht aendern.
        kopf_fehler = []
        for name, muster in KOPF_FELDER:
            a = re.search(muster, alt_roh, re.S)
            n = re.search(muster, neu_roh, re.S)
            if (a is None) != (n is None):
                kopf_fehler.append('%s: nur in %s vorhanden'
                                   % (name, 'alt' if a else 'neu'))
            elif a and normalize(a.group(1)) != normalize(n.group(1)):
                kopf_fehler.append('%s: alt=%r neu=%r'
                                   % (name, a.group(1)[:60], n.group(1)[:60]))
        if kopf_fehler:
            report.append((url + ' (Kopf)', ['  ' + f + '\n' for f in kopf_fehler]))
        else:
            kopf_ok += 1

    gesamt = gleich + abweichend + fehlend
    print()
    print('=' * 66)
    print('Seitenrumpf identisch: %d   abweichend: %d   fehlend: %d  (von %d)'
          % (gleich, abweichend, fehlend, gesamt))
    print('Titel, Description, Canonical unveraendert: %d von %d'
          % (kopf_ok, gesamt))
    print('=' * 66)

    if report:
        out = os.path.join(BLD, 'verify-diff.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            for url, diff in report:
                fh.write('\n' + '#' * 70 + '\n### %s\n' % url + '#' * 70 + '\n')
                fh.writelines(diff)
        print('Abweichungen: %s' % out)
        for url, diff in report[:5]:
            geaendert = sum(1 for line in diff if line[:1] in '+-')
            print('\n--- %s (%d Zeilen) ---' % (url, geaendert))
            for line in diff[:20]:
                print('   ' + line.rstrip('\n')[:150])

    return 0 if not report and fehlend == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
