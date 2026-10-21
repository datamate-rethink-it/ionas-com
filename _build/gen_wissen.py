#!/usr/bin/env python3
"""Holt die 150 Wissensartikel aus dem WordPress nach Hugo.

Quellen:
  wp/posts.json     REST-API: Metadaten, Schlagwoerter, Yoast-SEO-Felder
  wp/comments.json  REST-API: 280 freigegebene Kommentare
  wp/tags.json      REST-API: 380 Schlagwoerter (Name, Slug, Anzahl)
  reference-wissen/ gerenderte Seiten der Live-Installation

In _build/wp/comments.json und im passenden Referenz-Snapshot ist eine
Mailadresse nachtraeglich durch "[E-Mail-Adresse entfernt]" ersetzt: ein
Kommentator hatte 2017 seine eigene Adresse genannt, weil sein Name fuer
Spam-Versand missbraucht wurde. Siehe README, Abschnitt "Die
Wissensartikel".

Der Artikeltext kommt aus den *gerenderten* Seiten, nicht aus der REST-API:
nur dort steht die <span id="more-NNN">-Marke, an der WordPress den Teaser
fuer die Uebersichtsseite abschneidet. Die REST-API verschluckt sie. An
dieser Stelle wird Hugos <!--more-->-Trenner eingesetzt, damit .Summary
genau den bisherigen Teaser liefert.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import (BLD, PRJ, SRC, nicht_ausliefern, write,  # noqa: E402
                        yaml_block)

WP = os.environ.get('IONAS_WP') or os.path.join(BLD, 'wp')
REFW = os.environ.get('IONAS_REFW') or os.path.join(BLD, 'reference-wissen')
WEBROOT = os.path.join(PRJ, 'webroot')

ENTRY_OPEN = '<div class="entry">\n          '
ENTRY_CLOSE = '\n          <hr>\n        </div>'

MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
          'August', 'September', 'Oktober', 'November', 'Dezember']

# Stylesheets des WordPress, die das Aussehen der Artikel tatsaechlich
# beeinflussen. Alles andere (wp-block-library, global-styles, Emoji-CSS,
# simple-lightbox) wird nicht uebernommen: es gibt keine Gutenberg-Bloecke
# im Bestand, und die Lightbox ersetzt lightbox.js.
WP_CSS = [
    'wissen/wp-content/themes/ionas-wp/style.css',
    'wissen/wp-content/plugins/tablepress/css/default.min.css',
    # von default.min.css per @font-face eingebunden
    'wissen/wp-content/plugins/tablepress/css/tablepress.woff',
]

UPLOAD_SKIP = ('backwpup-0c97aa-logs', 'backwpup-0c97aa-temp',
               'nginx-helper', 'wp-statistics')

def jload(name):
    with open(os.path.join(WP, name), encoding='utf-8') as fh:
        return json.load(fh)


def q(value):
    return json.dumps(value, ensure_ascii=False)


def ref_body(slug):
    """Rumpf der gerenderten Einzelseite zwischen Header und Footer."""
    path = os.path.join(REFW, 'wissen', slug, 'index.html')
    with open(path, encoding='utf-8') as fh:
        html = fh.read()
    i = html.index('</header>') + len('</header>')
    j = html.index('<footer class="footer-1')
    return html[i:j]


def artikel_html(slug):
    """Artikeltext unveraendert aus der gerenderten Seite."""
    body = ref_body(slug)
    i = body.index(ENTRY_OPEN) + len(ENTRY_OPEN)
    j = body.index(ENTRY_CLOSE, i)
    text = body[i:j]
    if not re.search(r'<span id="more-\d+"></span>', text):
        raise ValueError('keine more-Marke in %s' % slug)
    return text


def inhaltsbilder(html):
    """Bilder eines Artikels mit Alternativtext - fuer die Bild-Sitemap."""
    out, gesehen = [], set()
    for m in re.finditer(r'<img\b[^>]*>', html):
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]+)"', tag)
        if not src:
            continue
        u = src.group(1)
        if u.startswith('/'):
            u = 'https://www.ionas.com' + u
        if u.startswith('http://www.ionas.com'):
            u = 'https://' + u[len('http://'):]
        if u in gesehen:
            continue
        gesehen.add(u)
        alt = re.search(r'\balt="([^"]*)"', tag)
        out.append((u, (alt.group(1) if alt else '').strip()))
    return out


def datum_lang(iso):
    """2016-10-08T17:24:11 -> '8. Oktober 2016 um 17:24 Uhr'"""
    d, t = iso.split('T')
    y, m, day = (int(x) for x in d.split('-'))
    return '%d. %s %d um %s Uhr' % (day, MONATE[m - 1], y, t[:5])


def schreibe_artikel(posts, tags_by_id, kommentar_zahl, teaser):
    for p in posts:
        y = p['yoast_head_json']
        graph = {n['@type']: n for n in y['schema']['@graph']}
        person = graph.get('Person', {})
        bild = graph.get('ImageObject', {}).get('url') or ''
        lesezeit = ''
        for item in (y.get('twitter_misc') or {}).items():
            if 'Lesezeit' in item[0]:
                lesezeit = item[1]

        slugs = [tags_by_id[t]['slug'] for t in p['tags'] if t in tags_by_id]
        artikel = graph.get('Article', {})
        bilder = inhaltsbilder(p['content']['rendered'])
        fm = ['---',
              'title: %s' % q(p['title']['rendered']),
              'date: %s' % p['date'],
              'lastmod: %s' % p['modified'],
              'url: %s' % q('/wissen/%s/' % p['slug']),
              'wissen: true',
              'wp_id: %d' % p['id'],
              'autor: %s' % q(person.get('name', '')),
              'autor_id: %s' % q(person.get('@id', '')),
              'beschreibung: %s' % q(y.get('description', '')),
              'titel_seo: %s' % q(y.get('title', '')),
              'canonical_url: %s' % q(y.get('canonical', '')),
              ]
        if bild:
            fm.append('bild: %s' % q(bild))
        if lesezeit:
            fm.append('lesezeit: %s' % q(lesezeit))
        if artikel.get('wordCount'):
            fm.append('wortanzahl: %d' % artikel['wordCount'])
        for sec in (artikel.get('articleSection') or [])[:1]:
            fm.append('kategorie: %s' % q(sec))
        if bilder:
            fm.append('bilder:')
            for src, alt in bilder:
                fm.append('  - loc: %s' % q(src))
                if alt:
                    fm.append('    text: %s' % q(alt))
        if kommentar_zahl.get(p['slug']):
            fm.append('kommentare: %d' % kommentar_zahl[p['slug']])
        if slugs:
            fm.append('tags:')
            fm += ['  - %s' % q(s) for s in sorted(slugs)]
        # Der Teaser der Uebersichtsseite steht wortgleich hier, statt ihn
        # ueber Hugos <!--more-->-Trenner aus dem Artikel abzuleiten:
        # WordPress haengt den "(mehr ...)"-Verweis bei 122 Artikeln als
        # eigenen Absatz an, bei 28 mitten in den letzten Absatz. Das ist
        # aus dem Volltext nicht zu rekonstruieren. Fuer neue Artikel kann
        # das Feld entfallen - dann greift Hugos .Summary (siehe
        # layouts/_partials/wissen-liste.html).
        if p['slug'] in teaser:
            fm.append(yaml_block('teaser', teaser[p['slug']].strip()))
        fm.append('---')
        write('content/wissen/%s.html' % p['slug'],
              '\n'.join(fm) + '\n' + artikel_html(p['slug']))


def schreibe_kommentare(comments, posts):
    """280 Kommentare als Datendatei, gruppiert nach Artikel."""
    slug_by_id = {p['id']: p['slug'] for p in posts}
    gruppen = {}
    for c in comments:
        slug = slug_by_id.get(c['post'])
        if not slug:
            continue
        gruppen.setdefault(slug, []).append(c)

    lines = ['# Die 280 freigegebenen Kommentare aus dem WordPress, nach',
             '# Artikel gruppiert und nach Datum sortiert. Stand 21.10.2026 -',
             '# der letzte Kommentar ist von 2019, es kommen keine neuen dazu.',
             '# Gerendert von layouts/_partials/wissen-kommentare.html.']
    gesamt = 0
    for slug in sorted(gruppen):
        cs = sorted(gruppen[slug], key=lambda c: c['date'])
        lines.append('%s:' % slug)
        for c in cs:
            lines.append('  - id: %d' % c['id'])
            lines.append('    autor: %s' % q(c['author_name']))
            lines.append('    datum: %s' % q(datum_lang(c['date'])))
            lines.append('    ' + yaml_block('html', c['content']['rendered'].strip(),
                                             indent='        ').replace('\n', '\n    '))
            gesamt += 1
    write('data/kommentare.yaml', '\n'.join(lines) + '\n')
    return len(gruppen), gesamt


def schreibe_tags(tags):
    """Nur Schlagwoerter mit Beitraegen; Name und WP-Term-ID fuer die Wolke."""
    genutzt = [t for t in tags if t['count'] > 0]
    lines = ['# Anzeigenamen und WordPress-Term-IDs der Schlagwoerter.',
             '# Hugo leitet Begriffsseiten aus den Slugs in der Frontmatter ab;',
             '# der Anzeigename steht hier, damit "backup" nicht zu "Backup"',
             '# normalisiert wird und die tag-link-NN-Klassen gleich bleiben.']
    for t in sorted(genutzt, key=lambda x: x['slug']):
        lines.append('%s:' % t['slug'])
        lines.append('  name: %s' % q(t['name']))
        lines.append('  id: %d' % t['id'])
        lines.append('  anzahl: %d' % t['count'])
    write('data/tagnamen.yaml', '\n'.join(lines) + '\n')
    return len(genutzt), len(tags) - len(genutzt)


def schreibe_archiv(posts):
    """Monatsseiten wie /wissen/2026/08/ - nur Monate mit Beitraegen."""
    monate = {}
    for p in posts:
        monate.setdefault(p['date'][:7], 0)
        monate[p['date'][:7]] += 1
    for ym, n in sorted(monate.items()):
        y, m = ym.split('-')
        titel = '%s %s' % (MONATE[int(m) - 1], y)
        write('content/wissen-archiv/%s.html' % ym,
              '\n'.join(['---',
                         'title: %s' % q('Archiv ' + titel),
                         'url: %s' % q('/wissen/%s/%s/' % (y, m)),
                         'wissen: true',
                         'monat: %s' % q(ym),
                         'monat_titel: %s' % q(titel),
                         'beitraege: %d' % n,
                         # Monatsarchive standen nie in der Sitemap; Yoast
                         # hielt sie aus dem Index. Das bleibt so.
                         'noindex: true',
                         '---']) + '\n')
    return len(monate)


def schreibe_index(posts):
    write('content/wissen/_index.html',
          '\n'.join(['---',
                     'title: "ionas Wissen"',
                     'url: "/wissen/"',
                     'wissen: true',
                     'beschreibung: "Wissensartikel von ionas - Ihr Online '
                     'Assistent: Anleitungen, Tipps und Hintergruende rund um '
                     'Computer, Software und Internet."',
                     'canonical_url: "https://www.ionas.com/wissen/"',
                     'titel_seo: "ionas Wissen"',
                     'outputs: ["html", "wissenfeed", "wissenpostsitemap", '
                     '"wissenpagesitemap", "wissensitemapindex"]',
                     '---']) + '\n')
    # Die Suchseite liegt in der Sektion (damit Layout und Sidebar passen),
    # bleibt aber aus Uebersicht, Feed und Vor/Zurueck-Navigation heraus.
    write('content/wissen/suche.html',
          '\n'.join(['---',
                     'title: "Suche"',
                     'url: "/wissen/suche/"',
                     'wissen: true',
                     'suche: true',
                     'noindex: true',
                     'build:',
                     '  list: never',
                     'beschreibung: "Volltextsuche in den Wissensartikeln von '
                     'ionas."',
                     '---']) + '\n')


def kopiere_assets(posts):
    """Uploads und die beiden noch gebrauchten WordPress-Stylesheets."""
    up_src = os.path.join(SRC, 'wissen/wp-content/uploads')
    # Alles, was in Artikeln vorkommt (auch srcset), plus die Originale.
    ref = set()
    for p in posts:
        html = p['content']['rendered']
        for m in re.finditer(r'(?:src|href)="([^"]+)"', html):
            ref.add(m.group(1))
        for m in re.finditer(r'srcset="([^"]+)"', html):
            for part in m.group(1).split(','):
                ref.add(part.strip().split(' ')[0])
    import urllib.parse
    wanted = set()
    for u in ref:
        for pre in ('https://www.ionas.com', 'http://www.ionas.com'):
            if u.startswith(pre):
                u = u[len(pre):]
        if '/wp-content/uploads/' in u:
            wanted.add(urllib.parse.unquote(
                u.split('/wp-content/uploads/', 1)[1].split('?')[0]))

    variante = re.compile(r'-\d+x\d+\.(jpg|jpeg|png|gif|webp)$', re.I)
    ohne = nicht_ausliefern()
    n = skip = 0
    for root, _dirs, files in os.walk(up_src):
        rel_dir = os.path.relpath(root, up_src)
        if rel_dir.split(os.sep)[0] in UPLOAD_SKIP:
            continue
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), up_src)
            # Originale behalten (koennen extern verlinkt sein), ungenutzte
            # Zwischengroessen nicht.
            if rel not in wanted and variante.search(rel):
                skip += 1
                continue
            if 'wissen/wp-content/uploads/' + rel in ohne:
                skip += 1
                continue
            dst = os.path.join(WEBROOT, 'wissen/wp-content/uploads', rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            n += 1
    for rel in WP_CSS:
        src = os.path.join(SRC, rel)
        dst = os.path.join(WEBROOT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n, skip


def main():
    posts = jload('posts.json')
    comments = jload('comments.json')
    tags = jload('tags.json')
    tags_by_id = {t['id']: t for t in tags}

    slug_by_id = {p['id']: p['slug'] for p in posts}
    kommentar_zahl = {}
    for c in comments:
        s = slug_by_id.get(c['post'])
        if s:
            kommentar_zahl[s] = kommentar_zahl.get(s, 0) + 1

    for d in ('content/wissen', 'content/wissen-archiv'):
        full = os.path.join(PRJ, d)
        if os.path.isdir(full):
            shutil.rmtree(full)

    schreibe_index(posts)
    teaser = jload('teasers.json')
    schreibe_artikel(posts, tags_by_id, kommentar_zahl, teaser)
    n_posts_k, n_komm = schreibe_kommentare(comments, posts)
    n_tags, n_leer = schreibe_tags(tags)
    n_monate = schreibe_archiv(posts)
    n_assets, n_skip = kopiere_assets(posts)

    print('Wissensbereich erzeugt:')
    print('  %3d Artikel in content/wissen/' % len(posts))
    print('  %3d Kommentare auf %d Artikeln -> data/kommentare.yaml'
          % (n_komm, n_posts_k))
    print('  %3d Schlagwoerter -> data/tagnamen.yaml (%d ohne Beitrag verworfen)'
          % (n_tags, n_leer))
    print('  %3d Monatsarchive in content/wissen-archiv/' % n_monate)
    print('  %3d Dateien nach webroot/ (%d ungenutzte Bildgroessen uebersprungen)'
          % (n_assets, n_skip))


if __name__ == '__main__':
    main()
