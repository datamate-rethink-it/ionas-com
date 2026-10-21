#!/usr/bin/env python3
"""Erzeugt content/ aus dem Referenz-Render und der Routentabelle."""
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import *

R = {r['route']: r for r in routes()}

CITY_TPL  = './staedte/pc-hilfe.php'
TOPIC_TPL = './themen/hilfethemen.php'

# Nicht uebernommen: nicht funktionsfaehige Werkzeuge/Formulare (nirgends
# verlinkt, nicht in der Sitemap, laufen schon in Produktion auf einen
# PHP-Fehler) und die vier Routen, die bewusst die 404-Seite ausliefern.
DROP = {
    '/test', '/portscan', '/lets-encrypt', '/vertragsabschluss', '/kontoaenderung',
    '/kontoaenderung2', '/laptop-hilfe', '/pc-hotline', '/vertragsabschluss2',
    # pages/weihnachten2015.php fehlt seit Jahren -> liefert live eine leere Seite
    '/weihnachten', '/computerhilfe-fuer-eltern',
}

# Route -> Dateiname in content/ (ohne Endung). Aliase stehen beim Primaerziel.
SIMPLE = {
    'startseite':                 ('_index',           []),
    '/dienstleistung':            ('dienstleistung',   []),
    '/assistenz':                 ('assistenz',        []),
    '/inspektion':                ('inspektion',       []),
    '/it-berater':                ('it-berater',       []),
    '/datensicherung':            ('datensicherung',   []),
    '/usb-stick':                 ('usb-stick',        ['/rescue-stick']),
    '/so-funktionierts':          ('so-funktionierts', []),
    '/supportsitzung':            ('supportsitzung',   []),
    '/pc-fernwartung':            ('pc-fernwartung',   []),
    '/kundenkomfort':             ('kundenkomfort',    []),
    '/preise':                    ('preise',           []),
    '/unternehmen':               ('unternehmen',      []),
    '/ueber-uns':                 ('ueber-uns',        []),
    '/team':                      ('team',             []),
    '/social-media':              ('social-media',     []),
    '/partner':                   ('partner',          []),
    '/bewertungen':               ('bewertungen',      []),
    '/presse':                    ('presse',           []),
    '/datenschutz':               ('datenschutz',      []),
    '/impressum':                 ('impressum',        []),
}


def fm(route, extra=None, aliases=(), url=None):
    """YAML-Frontmatter aus den Routendaten bauen."""
    r = R[route]
    out = ['---']
    out.append('title: %s' % json.dumps(r['title'], ensure_ascii=False))
    out.append('description: %s' % json.dumps(r['description'], ensure_ascii=False))
    if r['canonical']:
        out.append('canonical: %s' % json.dumps(r['canonical'], ensure_ascii=False))
    if r['keywords']:
        out.append('keywords: %s' % json.dumps(r['keywords'], ensure_ascii=False))
    if url:
        out.append('url: %s' % json.dumps(url, ensure_ascii=False))
    if aliases:
        out.append('aliases:')
        for a in aliases:
            out.append('  - %s' % json.dumps(a, ensure_ascii=False))
    for line in (extra or []):
        out.append(line)
    out.append('---')
    return '\n'.join(out) + '\n'


def body_of(route):
    return split_page(read_ref(route))[1]


def main():
    content = os.path.join(PRJ, 'content')
    if os.path.isdir(content):
        shutil.rmtree(content)

    made = {}

    # ---- einfache Seiten: Rumpf unveraendert aus dem Referenz-Render
    for route, (name, aliases) in SIMPLE.items():
        url = None if route == 'startseite' else route
        p = write('content/%s.html' % name, fm(route, aliases=aliases, url=url) + body_of(route))
        made[route] = p

    # ---- 404
    err = body_of('/laptop-hilfe')
    write('layouts/404.html',
          '{{ define "main" }}' + err + '{{ end }}\n')

    # ---- Staedte
    cities = {}
    for route, r in sorted(R.items()):
        if r['include'] != CITY_TPL or route in DROP:
            continue
        cities.setdefault(r['canonical'], []).append(route)

    n_city = 0
    for canonical, rts in sorted(cities.items()):
        prim = '/' + canonical.rstrip('/') if canonical != 'pc-hilfe/' else '/pc-hilfe'
        if prim not in rts:
            prim = sorted(rts, key=len)[0]
        aliases = sorted(x for x in rts if x != prim)
        r = R[prim]
        extra = ['stadt: %s' % json.dumps(r['stadtname'], ensure_ascii=False)]
        if r['lat']:
            extra.append('lat: %s' % r['lat'])
            extra.append('lon: %s' % r['lon'])
        for k in ('text1', 'text2'):
            if r[k]:
                extra.append(yaml_block(k, r[k]))
        if r['stadtname'] == '':
            write('content/pc-hilfe/_index.html', fm(prim, extra, aliases, url=prim))
        else:
            slug = prim.rsplit('/', 1)[1]
            write('content/pc-hilfe/%s.html' % slug, fm(prim, extra, aliases, url=prim))
        n_city += 1

    # ---- Hilfethemen
    n_topic = 0
    for route, r in sorted(R.items()):
        if r['include'] != TOPIC_TPL or route in DROP:
            continue
        extra = ['type: thema']
        for k in ('text1', 'text2'):
            if r[k]:
                extra.append(yaml_block(k, r[k]))
        rel = route.lstrip('/')
        write('content/%s.html' % rel, fm(route, extra, url=route))
        n_topic += 1

    print('content/ erzeugt:')
    print('  %3d einfache Seiten (davon 1 Startseite)' % len(SIMPLE))
    print('  %3d Staedteseiten (inkl. Uebersicht /pc-hilfe)' % n_city)
    print('  %3d Hilfethemen' % n_topic)
    print('  %3d Routen bewusst nicht uebernommen' % len(DROP))
    tot = len(SIMPLE) + n_city + n_topic
    print('  --> %d Seiten + %d verworfen = %d von %d Routen'
          % (tot, len(DROP), tot + len(DROP), len(R)))


if __name__ == '__main__':
    main()
