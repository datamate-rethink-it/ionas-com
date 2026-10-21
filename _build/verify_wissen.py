#!/usr/bin/env python3
"""Prueft die erzeugten Wissensseiten auf Vollstaendigkeit und Form.

Bis zum Umstieg verglich dieses Skript jede Seite Zeichen fuer Zeichen mit
einem Schnappschuss der WordPress-Installation. Das war die richtige
Pruefung fuer die Migration - und die falsche fuer den Betrieb danach: von
neun Vergleichen ueberlebten nur zwei eine normale Textaenderung. Schon ein
einziger neuer Artikel haette den Lauf rot gemacht, weil er die
Vor/Zurueck-Verweise des bisher neuesten Beitrags aendert. Ein Test, der
bei richtigem Verhalten Alarm schlaegt, erzieht dazu, Alarme zu ignorieren.

Geprueft wird jetzt, was unabhaengig vom Inhalt gelten muss:

  * jede Inhaltsdatei wird zu einer Seite
  * jede Seite hat Titel, Description, Canonical und Robots-Angabe
  * der Canonical zeigt auf die eigene Adresse
  * Artikelseiten haben H1, Artikelrumpf und Seitenleiste
  * die Kommentare aus data/kommentare.yaml stehen vollstaendig in den
    Seiten
  * jedes og:image zeigt auf eine Datei, die ausgeliefert wird

Der Schnappschuss des alten Stands liegt weiter in _build/reference-wissen/
- als Archiv der WordPress-Installation, nicht mehr als Pruefgrundlage.
Der Nachweis der Migration steht in der README und in der Git-Historie.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import PRJ  # noqa: E402

PUB = os.path.join(PRJ, 'public')
BASIS = 'https://www.ionas.com'


def lies(pfad):
    with open(pfad, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def kommentare_aus_daten():
    """slug -> Anzahl Kommentare, direkt aus data/kommentare.yaml."""
    pfad = os.path.join(PRJ, 'data', 'kommentare.yaml')
    if not os.path.isfile(pfad):
        return {}
    out, aktuell = {}, None
    for zeile in lies(pfad).split('\n'):
        if re.match(r'^[a-z0-9][\w-]*:$', zeile):
            aktuell = zeile[:-1]
            out[aktuell] = 0
        elif aktuell and zeile.startswith('  - id:'):
            out[aktuell] += 1
    return out


def frontmatter_beschreibung(slug):
    """Die gepflegte Description eines Artikels, falls es eine gibt."""
    pfad = os.path.join(PRJ, 'content', 'wissen', slug + '.html')
    if not os.path.isfile(pfad):
        return ''
    with open(pfad, encoding='utf-8') as fh:
        kopf = fh.read().split('\n---\n', 1)[0]
    m = re.search(r'^beschreibung:\s*"(.*)"$', kopf, re.M)
    return m.group(1) if m else ''


def artikel_slugs():
    """Slugs der Artikel aus content/wissen/ (ohne Sektion und Suchseite)."""
    out = []
    for pfad in sorted(glob.glob(os.path.join(PRJ, 'content', 'wissen', '*.html'))):
        name = os.path.basename(pfad)[:-5]
        if name in ('_index', 'suche'):
            continue
        out.append(name)
    return out


def main():
    fehler = []
    slugs = artikel_slugs()
    kommentare = kommentare_aus_daten()

    geprueft = 0
    ohne_beschreibung = []
    for slug in slugs:
        pfad = os.path.join(PUB, 'wissen', slug, 'index.html')
        if not os.path.isfile(pfad):
            fehler.append('%s: Seite fehlt in public/' % slug)
            continue
        html = lies(pfad)
        geprueft += 1

        for name, muster in (
                ('Titel', r'<title>(.+?)</title>'),
                ('Canonical', r'<link rel="canonical" href="(.+?)" />'),
                ('Robots', r"<meta name='robots' content='(.+?)' />")):
            if not re.search(muster, html, re.S):
                fehler.append('%s: %s fehlt' % (slug, name))

        # Die Description darf fehlen, wenn auch die Frontmatter keine hat -
        # 40 Artikel hatten schon im WordPress keine gepflegte Angabe. Ein
        # Fehler ist nur, wenn eine da ist und die Seite sie verliert.
        soll_besch = frontmatter_beschreibung(slug)
        hat_besch = bool(re.search(r'<meta name="description" content="(.+?)" />',
                                   html, re.S))
        if soll_besch and not hat_besch:
            fehler.append('%s: Description aus der Frontmatter fehlt in der Seite'
                          % slug)
        if not soll_besch:
            ohne_beschreibung.append(slug)

        m = re.search(r'<link rel="canonical" href="(.+?)" />', html)
        erwartet = '%s/wissen/%s/' % (BASIS, slug)
        if m and m.group(1) != erwartet:
            fehler.append('%s: Canonical zeigt auf %s statt %s'
                          % (slug, m.group(1), erwartet))

        for name, muster in (('H1', r'<h1[^>]*>'),
                             ('Artikelrumpf', r'<div class="entry">'),
                             ('Seitenleiste', r'<h3 class=.b_filter_head.>')):
            if not re.search(muster, html):
                fehler.append('%s: %s fehlt' % (slug, name))

        soll = kommentare.get(slug, 0)
        ist = len(re.findall(r'<div class="comment" id="comment-\d+"', html))
        if ist != soll:
            fehler.append('%s: %d Kommentare in der Seite, %d in der Datendatei'
                          % (slug, ist, soll))

    # og:image muss auf etwas zeigen, das es gibt - genau hier lag der
    # Fehler, durch den 13 Vorschaubilder beim Aufraeumen verloren gingen.
    ohne_bild = 0
    for pfad in glob.glob(os.path.join(PUB, 'wissen', '*', 'index.html')):
        for m in re.finditer(r'<meta property="og:image" content="([^"]+)"',
                             lies(pfad)):
            u = m.group(1)
            for p in ('https://www.ionas.com', 'http://www.ionas.com'):
                if u.startswith(p):
                    u = u[len(p):]
            if not u.startswith('/'):
                continue
            if not os.path.isfile(os.path.join(PUB, u.lstrip('/'))):
                ohne_bild += 1
                fehler.append('%s: og:image zeigt ins Leere (%s)'
                              % (os.path.basename(os.path.dirname(pfad)), u))

    summe_komm = sum(kommentare.values())
    in_seiten = sum(len(re.findall(r'<div class="comment" id="comment-\d+"',
                                   lies(os.path.join(PUB, 'wissen', s, 'index.html'))))
                    for s in slugs
                    if os.path.isfile(os.path.join(PUB, 'wissen', s, 'index.html')))

    print('=' * 66)
    print('Wissensartikel: %d Inhaltsdateien, %d Seiten erzeugt' % (len(slugs), geprueft))
    print('  Titel, Canonical, Robots                %s'
          % ('vollständig' if not [f for f in fehler if 'fehlt' in f] else 'LÜCKEN'))
    print('  ohne gepflegte Description              %d (schon im WordPress so)'
          % len(ohne_beschreibung))
    print('  Kommentare                              %d von %d in den Seiten'
          % (in_seiten, summe_komm))
    print('  og:image ohne Ziel                      %d' % ohne_bild)
    print('=' * 66)
    if fehler:
        print('%d Beanstandungen:' % len(fehler))
        for f in fehler[:20]:
            print('  ' + f)
        if len(fehler) > 20:
            print('  ... und %d weitere' % (len(fehler) - 20))
        return 1
    print('keine Beanstandungen')
    return 0


if __name__ == '__main__':
    sys.exit(main())
