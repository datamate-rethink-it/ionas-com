#!/usr/bin/env python3
"""Prueft alle seiteninternen Verweise in public/ auf Auflösbarkeit.

Beruecksichtigt src/href/srcset und url() in CSS, relativ und absolut.
Pfade, die erst der Webserver aufloest (siehe deploy/Caddyfile), gelten
als in Ordnung.
"""
import collections
import glob
import os
import re
import sys
import urllib.parse

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(PRJ, 'public')
HOSTS = ('https://www.ionas.com', 'http://www.ionas.com')

# Diese Adressen entstehen erst durch Regeln in deploy/Caddyfile.
VOM_WEBSERVER = {
    '/agb', '/wissen/feed', '/wissen/feed/', '/Datenschutz',
    '/drucker-druckt-nicht/', '/datensicherung-mit-windows-bordmitteln/',
    '/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/',
    # normpath entfernt den Slash am Ende, deshalb hier ohne
    '/wissen/wlan-passwort-auslesen-so-einfach-gehts/'
    'wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel',
}
# Schon vor der Migration kaputt, Dateien fehlen im Quellbaum.
BEKANNT_KAPUTT = {
    '/downloads/CV_RalfDyllick-Brenzinger.pdf',
    '/downloads/CV_ChristophDyllick-Brenzinger.pdf',
    '/startup/common-files/img/header/img-3.jpg',
    '/wissen/startup/common-files/icons/menu-icon@2x.png',
    '/wissen/startup/common-files/icons/menu-icon-dark@2x.png',
    '/static/fonts/glyphicons-halflings-regular.eot',
    '/static/fonts/glyphicons-halflings-regular.svg',
    '/static/fonts/glyphicons-halflings-regular.ttf',
    '/static/fonts/glyphicons-halflings-regular.woff2',
    # fehlerhafte Verweise in den Artikeltexten bzw. auf /inspektion
    '/inspektion/assistenz',
    # href="www.datamate.org/hero" ohne Protokoll -> wird relativ aufgelöst
    '/wissen/acronis-cloud-backup-und-wiederherstellung/www.datamate.org/hero',
    # Rueckwaerts-Verweis der 404-Seite, kein echter Pfad
    '/javascript:history.go(-1)',
}



def meta_bild_verweise(text):
    """URLs aus <meta ... content="...">, soweit es Bildangaben sind.

    og:image und twitter:image zeigen auf echte Dateien, tauchen aber in
    keinem src/href auf. Ohne diese Funktion haelt der Scanner das Bild
    fuer verwaist - und das og:image der Startseite zeigte jahrelang auf
    eine Datei, die es nie gab, ohne dass es jemandem auffiel.
    """
    out = []
    for tag in re.findall(r'<meta\b[^>]*>', text, re.I):
        if not re.search(r'(?:property|name)\s*=\s*["\'][^"\']*image[^"\']*["\']', tag, re.I):
            continue
        m = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if m:
            out.append(m.group(1))
    return out


def vorhanden(pfad):
    f = os.path.join(PUB, pfad.lstrip('/'))
    return (os.path.isfile(f) or os.path.isfile(os.path.join(f, 'index.html'))
            or os.path.isdir(f))


def main():
    muster = [re.compile(r'''(?:src|href)\s*=\s*["']([^"']+)["']'''),
              re.compile(r'url\(\s*["\']?([^"\')?#]+)')]
    refs = collections.defaultdict(set)
    for f in (glob.glob(PUB + '/**/*.html', recursive=True)
              + glob.glob(PUB + '/**/*.css', recursive=True)):
        with open(f, encoding='utf-8', errors='replace') as fh:
            text = fh.read()
        basis = '/' + os.path.relpath(os.path.dirname(f), PUB).replace('\\', '/')
        if basis == '/.':
            basis = '/'
        roh = set()
        for m in muster:
            roh.update(x.group(1) for x in m.finditer(text))
        for m in re.finditer(r'srcset\s*=\s*["\']([^"\']+)["\']', text):
            roh.update(p.strip().split(' ')[0] for p in m.group(1).split(','))
        roh.update(meta_bild_verweise(text))
        for u in roh:
            u = u.strip()
            for h in HOSTS:
                if u.startswith(h):
                    u = u[len(h):]
            if not u or u.startswith(('data:', 'mailto:', 'tel:', '#', '//', 'http')):
                continue
            if not u.startswith('/'):
                u = os.path.normpath(os.path.join(basis, u))
            refs[urllib.parse.unquote(u.split('?')[0].split('#')[0])].add(f[len(PUB):])

    kaputt = {t: v for t, v in refs.items()
              if not vorhanden(t) and t not in VOM_WEBSERVER}
    neu = {t: v for t, v in kaputt.items() if t not in BEKANNT_KAPUTT}
    print('geprüfte Zielpfade: %d' % len(refs))
    print('  vom Webserver aufgelöst: %d' % len(VOM_WEBSERVER))
    print('  schon vorher kaputt:     %d' % (len(kaputt) - len(neu)))
    print('  NEU kaputt:              %d' % len(neu))
    for t, v in sorted(neu.items()):
        print('    %-62s <- %d Seite(n), z.B. %s' % (t[:62], len(v), sorted(v)[0]))
    return 1 if neu else 0


if __name__ == '__main__':
    sys.exit(main())
