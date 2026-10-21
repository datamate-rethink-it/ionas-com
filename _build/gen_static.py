#!/usr/bin/env python3
"""Kopiert die benoetigten Assets nach webroot/ und erzeugt die Sitemap-Daten."""
import os, re, sys, json, shutil, glob
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import *

WEBROOT = os.path.join(PRJ, 'webroot')

# Ganze Verzeichnisse, die uebernommen werden.
COPY_DIRS = ['images', 'ionas-neu', 'static', 'downloads', 'senderlogos']
COPY_FILES = ['robots.txt', 'ads.txt', 'themen/windows_support.png',
              'sitemap/sitemap_style.xsl']

# Nachweislich toter Ballast (von keiner ausgelieferten Seite und keinem
# eingebundenen Stylesheet referenziert):
#   staedte/    15 MB Stadtfotos - nur aus auskommentiertem Code verlinkt
#   static/js/parallax/*.jpg|png|gif  20 MB Demobilder der Parallax-Library
#   demo/ storage/ phpmailer/ cronjob/ external/ sitemap/*.php
EXCLUDE_RE = re.compile(
    r'^static/js/parallax/.*\.(jpg|jpeg|png|gif)$'
    r'|^static/pdf-creation/'
    r'|^static/formsAndValidation/'
    r'|\.php$',
    re.I)


def copy_assets():
    if os.path.isdir(WEBROOT):
        shutil.rmtree(WEBROOT)
    n = skipped = 0
    for d in COPY_DIRS:
        for root, _dirs, files in os.walk(os.path.join(SRC, d)):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, SRC)
                if EXCLUDE_RE.search(rel):
                    skipped += 1
                    continue
                dst = os.path.join(WEBROOT, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(full, dst)
                n += 1
    for f in COPY_FILES:
        src = os.path.join(SRC, f)
        if not os.path.isfile(src):
            print('  WARNUNG: %s fehlt' % f)
            continue
        # themen/windows_support.png bleibt unter seinem alten Pfad
        dst = os.path.join(WEBROOT, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    # sitemap.xml ist ein Index und zeigt auch auf das WordPress -> unveraendert
    shutil.copy2(os.path.join(SRC, 'sitemap.xml'), os.path.join(WEBROOT, 'sitemap.xml'))
    n += 1
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _d, fs in os.walk(WEBROOT) for f in fs)
    print('webroot/: %d Dateien, %.1f MB (%d Dateien als toter Ballast uebersprungen)'
          % (n, size / 1e6, skipped))


def sitemap_meta():
    """priority/changefreq/lastmod aus der alten main.xml uebernehmen."""
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    tree = ET.parse(os.path.join(SRC, 'sitemap', 'main.xml'))
    meta = {}
    for u in tree.getroot().findall('s:url', ns):
        loc = u.findtext('s:loc', '', ns)
        path = loc.replace('https://www.ionas.com', '') or '/'
        meta[path] = {
            'priority': u.findtext('s:priority', '0.5', ns),
            'changefreq': u.findtext('s:changefreq', 'monthly', ns),
            'lastmod': u.findtext('s:lastmod', '', ns),
        }
    return meta


def main():
    copy_assets()
    meta = sitemap_meta()

    # Nicht-Seiten-URLs (PDFs) fuer die Sitemap, ohne die drei, die schon
    # vor der Migration 404 liefern.
    DEAD = {'/downloads/CV_RalfDyllick-Brenzinger.pdf',
            '/downloads/CV_ChristophDyllick-Brenzinger.pdf',
            '/static/presse/1510_Gewinner Mainzer Wirtschaftspreis-2015.pdf'}
    extra = []
    for path, m in sorted(meta.items()):
        if not re.search(r'\.(pdf|exe|xpi)$', path, re.I):
            continue
        if path in DEAD:
            continue
        extra.append({'loc': path, **m})
    # /agb liefert downloads/AGB-ionas.pdf (Rewrite im Webserver)
    if '/agb' in meta:
        extra.append({'loc': '/agb', **meta['/agb']})
    extra.sort(key=lambda e: e['loc'])

    lines = ['# Sitemap-Eintraege, die keine Hugo-Seiten sind (PDFs, /agb).',
             '# priority/changefreq/lastmod uebernommen aus der alten sitemap/main.xml.',
             'urls:']
    for e in extra:
        lines.append('  - loc: %s' % json.dumps(e['loc'], ensure_ascii=False))
        lines.append('    priority: "%s"' % e['priority'])
        lines.append('    changefreq: %s' % e['changefreq'])
        if e['lastmod']:
            lines.append('    lastmod: "%s"' % e['lastmod'])
    write('data/sitemap_extra.yaml', '\n'.join(lines) + '\n')
    print('data/sitemap_extra.yaml: %d Nicht-Seiten-URLs (%d tote entfernt)'
          % (len(extra), len(DEAD)))

    # Sitemap-Metadaten in die Frontmatter der Seiten nachtragen
    patched = nomatch = []
    patched, nomatch = [], []
    for p in glob.glob(os.path.join(PRJ, 'content', '**', '*.html'), recursive=True):
        with open(p, encoding='utf-8') as fh:
            txt = fh.read()
        m = re.search(r'^---\n(.*?)\n---\n', txt, re.S)
        if not m:
            continue
        head = m.group(1)
        um = re.search(r'^url: "(.*?)"$', head, re.M)
        url = um.group(1) if um else '/'
        cands = [url, url.rstrip('/') or '/']
        cands += re.findall(r'^  - "(.*?)"$', head, re.M)   # Aliase
        key = next((c for c in cands if c in meta), None)
        if key is None:
            nomatch.append(url)
            md = {'priority': '0.5', 'changefreq': 'monthly', 'lastmod': ''}
            txt = txt.replace(m.group(0), '---\n' + head + '\n'
                              + 'sitemap_loc: %s\n' % json.dumps(url, ensure_ascii=False)
                              + 'sitemap_priority: "0.5"\n'
                              + 'sitemap_changefreq: monthly\n---\n', 1)
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(txt)
            continue
        md = meta[key]
        add = ['sitemap_loc: %s' % json.dumps(url, ensure_ascii=False),
               'sitemap_priority: "%s"' % md['priority'],
               'sitemap_changefreq: %s' % md['changefreq']]
        if md['lastmod']:
            add.append('sitemap_lastmod: "%s"' % md['lastmod'])
        txt = txt.replace(m.group(0),
                          '---\n' + head + '\n' + '\n'.join(add) + '\n---\n', 1)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(txt)
        patched.append(url)
    print('Sitemap-Metadaten gesetzt: %d Seiten' % len(patched))
    if nomatch:
        print('  nicht in der alten Sitemap (erhalten Standardwerte): %s'
              % ', '.join(sorted(nomatch)))

    # ---- Sitemap-Template
    write('layouts/home.mainsitemap.xml', """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="//www.ionas.com/sitemap/sitemap_style.xsl"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{{- range $p := sort site.Pages "Params.sitemap_loc" }}{{ with $p.Params.sitemap_loc }}
 <url>
  <loc>https://www.ionas.com{{ . }}</loc>
  <priority>{{ $p.Params.sitemap_priority | default "0.5" }}</priority>
  <changefreq>{{ $p.Params.sitemap_changefreq | default "monthly" }}</changefreq>
{{- with $p.Params.sitemap_lastmod }}
  <lastmod>{{ . }}</lastmod>
{{- end }}
 </url>
{{- end }}{{ end }}
{{- range hugo.Data.sitemap_extra.urls }}
 <url>
  <loc>https://www.ionas.com{{ .loc }}</loc>
  <priority>{{ .priority }}</priority>
  <changefreq>{{ .changefreq }}</changefreq>
{{- with .lastmod }}
  <lastmod>{{ . }}</lastmod>
{{- end }}
 </url>
{{- end }}
</urlset>
""")
    print('layouts/home.mainsitemap.xml geschrieben')


if __name__ == '__main__':
    main()
