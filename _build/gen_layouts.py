#!/usr/bin/env python3
"""Erzeugt hugo.toml, baseof und die Partials byte-genau aus dem Referenz-Render."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import *

R = {r['route']: r for r in routes()}

# ---------------------------------------------------------------- hugo.toml
write('hugo.toml', '''baseURL = 'https://www.ionas.com/'
locale = 'de-de'
title = 'ionas - Ihr Online Assistent'
defaultContentLanguage = 'de'

# Die Seite ist ein Archiv: keine Taxonomien, kein RSS. Die sitemap.xml
# ist ein Index, der auch auf das WordPress unter /wissen zeigt, und liegt
# deshalb als statische Datei in static/ - erzeugt wird nur sitemap/main.xml.
disableKinds = ['taxonomy', 'term', 'rss', 'sitemap']

# Umlaut-URLs wie /pc-hilfe/muenchen -> /pc-hilfe/münchen muessen erhalten
# bleiben, sonst brechen indexierte Landingpages weg.
removePathAccents = false
disablePathToLower = true

disableHugoGeneratorInject = true  # kein <meta name="generator">
enableRobotsTXT = false  # robots.txt kommt unveraendert aus webroot/

# Alles, was unveraendert unter / ausgeliefert wird, liegt in webroot/.
# (Hugos Standardname waere static/ - das waere hier verwirrend, weil die
# Seite selbst einen Pfad /static/ fuer CSS und JS benutzt.)
staticDir = 'webroot'

[outputs]
home = ['html', 'mainsitemap']

# sitemap/main.xml - gleicher Pfad wie bisher, damit sitemap.xml weiter stimmt
[outputFormats.mainsitemap]
mediaType = 'application/xml'
path = 'sitemap'
baseName = 'main'
isPlainText = true
notAlternative = true

[markup.goldmark.renderer]
unsafe = true

# Die Inhalte sind reine HTML-Dateien (direkt aus den alten PHP-Templates
# uebernommen), kein Markdown. Hugo sperrt text/html als Inhaltsformat seit
# 0.16x per Default - hier unbedenklich, weil alle Inhalte aus dem eigenen
# Repository kommen und kein fremder Autor schreibt.
[security]
allowContent = ['^text/html$', '^text/markdown$']

[minify]
disableHTML = true
''')

# ---------------------------------------------------------------- baseof
head, _, tail = split_page(read_ref('/pc-hilfe/mainz'))
m = R['/pc-hilfe/mainz']

# Variable Kopfbestandteile parametrisieren
head = head.replace(
    "<meta name=\"description\" content='%s' />" % m['description'],
    "<meta name=\"description\" content='{{ .Params.description }}' />")
head = head.replace(
    '<title>%s</title>' % m['title'],
    '<title>{{ .Title }}</title>')
head = head.replace(
    '<meta property="og:description" content="%s" />' % m['description'],
    '<meta property="og:description" content="{{ .Params.description }}" />')
canon = ('        <link rel="canonical" href="https://www.ionas.com/%s" />\n'
         '        <meta name="robots" content="noarchive" />\n' % m['canonical'])
assert canon in head, 'Canonical-Block nicht gefunden'
head = head.replace(canon,
    '{{ with .Params.canonical }}        '
    # Go normalisiert URLs in href-Attributen und wuerde Umlaute zu %c3%bc
    # kodieren - auch bei safeURL. Deshalb das ganze Tag als safeHTML bauen,
    # damit /pc-hilfe/koeln & Co. weiter mit rohem Umlaut im canonical stehen.
    '{{ printf `<link rel="canonical" href="https://www.ionas.com/%s" />` . | safeHTML }}\n'
    '        <meta name="robots" content="noarchive" />\n{{ end }}')

# header.php -> Partial
hi = head.index('<header class="header-10">')
site_head, header_html = head[:hi], head[hi:]
write('layouts/_partials/site-header.html', header_html)

# Fuss: footer.php + Skriptblock. Der Startseiten-Zusatzblock steckt
# zwischen </footer> und dem naechsten <script> und wandert ins Partial.
home_tail = split_page(read_ref('startseite'))[2]
SCRIPTS = '<script src="/static/js/jquery-1.10.2.min.js"></script>'

def cut_tail(t):
    """Fuss in Footer-Element, Startseitenzusatz und Skriptblock zerlegen."""
    i = t.index('</footer>') + len('</footer>')
    j = t.index(SCRIPTS)
    return t[:i], t[i:j], t[j:]

foot_common, mid, foot_rest = cut_tail(tail)
home_foot, home_extra, home_rest = cut_tail(home_tail)
assert home_foot == foot_common, 'Footer weicht zwischen Startseite und Unterseite ab'
assert home_rest == foot_rest, 'Skriptblock weicht zwischen Startseite und Unterseite ab'
assert mid.strip() == '', 'Unterseite hat unerwarteten Block hinter </footer>'
assert home_extra.strip().startswith('<section'), 'Startseiten-Zusatzblock nicht erkannt'

write('layouts/_partials/site-footer.html', foot_common)
write('layouts/_partials/home-seo.html', home_extra)

# site_head und der Skriptblock enthalten unpaarige Tags (<html>, <body>,
# <div class="page-wrapper">) und koennen deshalb nicht in Partials liegen -
# html/template verlangt dort balancierten Code. Sie stehen direkt im baseof.
write('layouts/baseof.html',
      site_head
      + '{{ partial "site-header.html" . }}'
      + '{{ block "main" . }}{{ end }}'
      + '{{ partial "site-footer.html" . }}'
      + mid
      + '{{ if .IsHome }}{{ partial "home-seo.html" . }}{{ end }}'
      + foot_rest)

# ---------------------------------------------------------------- einfache Layouts
write('layouts/page.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')
write('layouts/home.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')
write('layouts/section.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')

print('Layouts erzeugt:')
for p in ('hugo.toml', 'layouts/baseof.html', 'layouts/_partials/site-header.html',
          'layouts/_partials/site-footer.html', 'layouts/_partials/home-seo.html',
          'layouts/page.html'):
    print('  %7d B  %s' % (os.path.getsize(os.path.join(PRJ, p)), p))
