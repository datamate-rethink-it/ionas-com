#!/usr/bin/env python3
"""Listet Dateien in public/, auf die keine ausgelieferte Seite verweist.

Beruecksichtigt src/href/srcset in HTML, url() in CSS, <loc>/<image:loc>
in den Sitemaps und relative wie absolute Pfade.
"""
import collections
import glob
import os
import re
import sys
import urllib.parse

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(PRJ, 'public')
BLD = os.path.join(PRJ, '_build')
HOSTS = ('https://www.ionas.com', 'http://www.ionas.com')

# Dateien, die der Scanner nicht als verlinkt erkennt, die aber gebraucht
# werden. Der Scanner liest src/href/srcset, url() und <loc> - diese drei
# haengen an anderen Mechanismen:
BEHALTEN = {
    # per <?xml-stylesheet?> in sitemap.xml eingebunden
    '/sitemap/sitemap_style.xsl',
    # wird vom Webserver unter /agb ausgeliefert (siehe deploy/Caddyfile)
    '/downloads/AGB-ionas.pdf',
}


def verweise():
    out = set()
    muster = [
        re.compile(r'''(?:src|href)\s*=\s*["']([^"']+)["']'''),
        re.compile(r'url\(\s*["\']?([^"\')?#]+)'),
        re.compile(r'<(?:loc|image:loc)>([^<]+)</'),
    ]
    dateien = (glob.glob(PUB + '/**/*.html', recursive=True)
               + glob.glob(PUB + '/**/*.css', recursive=True)
               + glob.glob(PUB + '/**/*.xml', recursive=True))
    for f in dateien:
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
        for u in roh:
            u = u.strip()
            for h in HOSTS:
                if u.startswith(h):
                    u = u[len(h):]
            if not u or u.startswith(('data:', 'mailto:', 'tel:', '#', '//')):
                continue
            if u.startswith('http'):
                continue
            if not u.startswith('/'):                 # relativ zur Seite
                u = os.path.normpath(os.path.join(basis, u))
            out.add(urllib.parse.unquote(u.split('?')[0].split('#')[0]))
    return out


def main():
    genutzt = verweise()
    verwaist = []
    gesamt = 0
    for root, _dirs, files in os.walk(PUB):
        for f in files:
            pfad = os.path.join(root, f)
            rel = '/' + os.path.relpath(pfad, PUB).replace('\\', '/')
            if rel.endswith(('.html', '.xml', '.txt')) or rel.startswith('/pagefind/'):
                continue
            groesse = os.path.getsize(pfad)
            gesamt += groesse
            if rel not in genutzt and rel not in BEHALTEN:
                verwaist.append((rel, groesse))

    vsum = sum(s for _, s in verwaist)
    print('ausgelieferte Assets: %d Dateien, %.1f MB' % (
        sum(1 for _, _, fs in os.walk(PUB) for _ in fs), gesamt / 1e6))
    print('davon ohne Verweis:   %d Dateien, %.1f MB\n' % (len(verwaist), vsum / 1e6))

    nach_ort = collections.Counter()
    anzahl = collections.Counter()
    for rel, s in verwaist:
        teile = rel.split('/')
        ort = '/'.join(teile[1:3]) if len(teile) > 3 else teile[1]
        nach_ort[ort] += s
        anzahl[ort] += 1
    print('nach Ort:')
    for ort, s in nach_ort.most_common(15):
        print('  %7.2f MB  %5d  /%s' % (s / 1e6, anzahl[ort], ort))
    print('\ngroesste Einzeldateien:')
    for rel, s in sorted(verwaist, key=lambda x: -x[1])[:10]:
        print('  %6.2f MB  %s' % (s / 1e6, rel))
    if len(sys.argv) > 1 and sys.argv[1] == '--schreiben':
        ziel = os.path.join(BLD, 'nicht-ausliefern.txt')
        with open(ziel, 'w', encoding='utf-8') as fh:
            fh.write('# Dateien aus dem alten Quellbaum, auf die keine\n'
                     '# ausgelieferte Seite verweist. gen_static.py und\n'
                     '# gen_wissen.py kopieren sie nicht nach webroot/.\n'
                     '#\n'
                     '# Erzeugt von _build/verwaiste_assets.py --schreiben,\n'
                     '# jeweils gegen ein vollstaendig gebautes public/.\n'
                     '# %d Dateien, %.1f MB\n' % (len(verwaist), vsum / 1e6))
            for rel, _s in sorted(verwaist):
                fh.write('%s\n' % rel)
        print('\nListe geschrieben: _build/nicht-ausliefern.txt')


if __name__ == '__main__':
    main()
