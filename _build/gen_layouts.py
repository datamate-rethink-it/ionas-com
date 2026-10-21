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
disableKinds = ['taxonomy', 'rss', 'sitemap']

# Umlaut-URLs wie /pc-hilfe/muenchen -> /pc-hilfe/münchen muessen erhalten
# bleiben, sonst brechen indexierte Landingpages weg.
removePathAccents = false
titleCaseStyle = 'none'
disablePathToLower = true

disableHugoGeneratorInject = true  # kein <meta name="generator">
enableRobotsTXT = false  # robots.txt kommt unveraendert aus webroot/

# Alles, was unveraendert unter / ausgeliefert wird.
# (Hugos Standardname waere static/ - das waere hier verwirrend, weil die
# Seite selbst einen Pfad /static/ fuer CSS und JS benutzt.)
#
#   webroot/        der uebernommene Dateibestand. Wird von
#                   _build/gen_static.py neu erzeugt - nichts hineinlegen,
#                   was man behalten will.
#   webroot-eigen/  selbst geschriebene Dateien (lightbox.js, suche.js),
#                   wird nie neu erzeugt. Hugo mischt beide Verzeichnisse.
staticDir = ['webroot', 'webroot-eigen']

[outputs]
home = ['html', 'mainsitemap']

# Schlagwoerter der Wissensartikel. Die Begriffsseiten lagen im WordPress
# unter /wissen/tag/<slug>/ und sind aus jedem Artikel verlinkt; die
# Uebersicht aller Begriffe (/tags/) gab es nie -> Kind 'taxonomy' aus.
[taxonomies]
tag = 'tags'

[permalinks.term]
tags = '/wissen/tag/:slug/'

# RSS-Feed der Wissensartikel. Die URL /wissen/feed/ ist im Footer jeder
# Seite verlinkt, deshalb landet die Datei als index.xml in diesem Ordner.
# Die Datei landet als /wissen/feed.xml; der Webserver liefert sie unter
# der bisherigen Adresse /wissen/feed/ aus (siehe deploy/Caddyfile).
[outputFormats.wissenfeed]
mediaType = 'application/rss+xml'
baseName = 'feed'
isPlainText = true
notAlternative = true

# Die drei Sitemaps, die bisher Yoast SEO erzeugt hat. Der Index
# /wissen/sitemap_index.xml ist in der Search Console eingetragen und
# bleibt deshalb unter derselben Adresse erreichbar.
[outputFormats.wissenpostsitemap]
mediaType = 'application/xml'
baseName = 'post-sitemap'
isPlainText = true
notAlternative = true

[outputFormats.wissenpagesitemap]
mediaType = 'application/xml'
baseName = 'page-sitemap'
isPlainText = true
notAlternative = true

[outputFormats.wissensitemapindex]
mediaType = 'application/xml'
baseName = 'sitemap_index'
isPlainText = true
notAlternative = true

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
# Der <head> des alten PHP-Teils. Die Wissensartikel haben einen eigenen
# (Yoast-Metadaten, Theme-Stylesheet) - siehe kopf-wissen.html.
# Die Schrift lag bisher bei fonts.googleapis.com - damit ging bei jedem
# Seitenaufruf die Besucher-IP an Google. Jetzt lokal, siehe
# webroot-eigen/static/css/fonts.css.
GOOGLE_FONT = ("<link href='//fonts.googleapis.com/css?family=Open+Sans+Condensed"
               ":300,700' rel='stylesheet' type='text/css' />")
EIGENE_FONT = '<link rel="stylesheet" href="/static/css/fonts.css" />'
assert GOOGLE_FONT in site_head, 'Google-Fonts-Zeile nicht gefunden'
site_head = site_head.replace(GOOGLE_FONT, EIGENE_FONT)
# --- toter Code im Kopf ----------------------------------------------
# Google+ ist seit April 2019 abgeschaltet, Alexa seit Mai 2022. Die
# Zeilen stehen seitdem wirkungslos in jeder Seite.
#
# Nicht entfernt werden google-site-verification und msvalidate.01: daran
# kann die Bestaetigung der Property in der Search Console bzw. bei Bing
# haengen. Ein Entfernen wuerde erst Monate spaeter auffallen.
TOT = [
    '        <link href="https://plus.google.com/116393713732767018174" rel="author" />\n',
    '        <link href="https://plus.google.com/+ionasOHGMainz/" rel="publisher" />\n',
    '        <meta name="alexaVerifyID" content="Qsa4yU-EGFDYpT5A4pJZg40o_LA"/> <!-- Amazon Alexa -->\n',
]
for zeile in TOT:
    assert zeile in site_head, 'tote Zeile nicht gefunden: %s' % zeile[:60]
    site_head = site_head.replace(zeile, '')

# --- og:image --------------------------------------------------------
# Zeigte ueber http auf /images/ionas-logo-facebook.jpg - eine Datei, die
# es nie gab (404 auch auf der alten Seite). Jede Freigabe bei Facebook,
# LinkedIn oder WhatsApp blieb deshalb ohne Vorschaubild. Jetzt auf das
# einzige eigene Bild, das Facebooks Mindestmass erfuellt: 1000x479.
OG_ALT = ('<meta property="og:image" '
          'content="http://www.ionas.com/images/ionas-logo-facebook.jpg" />')
OG_NEU = ('<meta property="og:image" '
          'content="https://www.ionas.com/static/presse/ionas_logo_freigestellt.png" />')
assert OG_ALT in site_head, 'og:image-Zeile nicht gefunden'
site_head = site_head.replace(OG_ALT, OG_NEU)

write('layouts/_partials/kopf-ionas.html', site_head)

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
# Schlagwort- und Archivseiten tragen kein eigenes Frontmatter, deshalb
# wird die Zugehoerigkeit zum Wissensbereich hier aus Sektion und Typ
# mitbestimmt.
write('layouts/baseof.html',
      '{{ $wissen := or .Params.wissen (eq .Section "wissen") '
      '(eq .Section "wissen-archiv") (eq .Type "tags") }}'
      '{{ if $wissen }}{{ partial "kopf-wissen.html" . }}'
      '{{ else }}{{ partial "kopf-ionas.html" . }}{{ end }}'
      + '{{ partial "site-header.html" . }}'
      + '{{ block "main" . }}{{ end }}'
      + '{{ partial "site-footer.html" . }}'
      + mid
      + '{{ if .IsHome }}{{ partial "home-seo.html" . }}{{ end }}'
      + foot_rest.replace('</body>',
          '{{ if $wissen }}<script src="/static/js/lightbox.js" defer></script>\n{{ end }}'
          '{{ if .Params.suche }}<script src="/static/js/suche.js" type="module"></script>\n{{ end }}</body>'))

# ---------------------------------------------------------------- einfache Layouts
write('layouts/page.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')
write('layouts/home.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')
write('layouts/section.html', '{{ define "main" }}{{ .Content }}{{ end }}\n')

print('Layouts erzeugt:')
for p in ('hugo.toml', 'layouts/baseof.html', 'layouts/_partials/site-header.html',
          'layouts/_partials/site-footer.html', 'layouts/_partials/home-seo.html',
          'layouts/page.html'):
    print('  %7d B  %s' % (os.path.getsize(os.path.join(PRJ, p)), p))
