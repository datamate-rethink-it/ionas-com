#!/usr/bin/env python3
"""Uebersetzt staedte/pc-hilfe.php und themen/hilfethemen.php in Hugo-Layouts.

Die PHP-Dateien werden von PHP selbst tokenisiert (tok.php), damit die
Grenzen zwischen Inline-HTML und PHP-Code exakt stimmen - mehrere der
PHP-Bloecke sind durch /* */ ueberspannt und per Regex nicht sicher zu
trennen. Jeder PHP-Abschnitt wird hier einzeln auf sein Hugo-Pendant
abgebildet; unbekannte Abschnitte brechen den Lauf ab.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import *

TOK = os.path.join(BLD, 'tok.php')

BERLIN_DISTRICTS = ['Reinickendorf', 'Charlottenburg', 'Pankow',
                    'Prenzlauer Berg', 'Steglitz', 'Tempelhof']


def tokenize(relpath):
    out = subprocess.run(['php', TOK, relpath], cwd=SRC, capture_output=True,
                         text=True, check=True).stdout
    return json.loads(out)


# PHP-Abschnitt (normalisiert) -> Hugo-Ersatz
DISTRICT_LIST = ' '.join('"%s"' % d for d in BERLIN_DISTRICTS)

# Breadcrumb: Berliner Ortsteile bekommen eine Berlin-Stufe davor, die
# Uebersichtsseite (canonical == "pc-hilfe/") gar keine.
# Go normalisiert URLs in href-Attributen und wuerde Umlaute zu %c3%bc
# kodieren - auch bei safeURL. Deshalb wird das Anker-Tag als safeHTML
# gebaut, damit /pc-hilfe/koeln & Co. den rohen Umlaut behalten.
CRUMB = (
    '{{ if in (slice ' + DISTRICT_LIST + ') .Params.stadt }}'
    '&nbsp; / &nbsp; <a href="/pc-hilfe/berlin">Berlin</a>{{ end }}'
    '{{ if ne .Params.canonical "pc-hilfe/" }}&nbsp; / &nbsp; '
    '{{ printf `<a href="/%s">%s</a>` .Params.canonical .Params.stadt | safeHTML }}'
    '{{ end }}'
)

# PHP-Abschnitt (Zeilennummer in der Quelle) -> Hugo-Ersatz
CITY_MAP = {
    6: CRUMB,
    23: '{{ .Params.stadt }}',
    # Zeile 29 war ein Entwickler-Kommentar ("Mainz - Mainz - pc-hilfe/mainz")
    # im HTML-Quelltext. Bewusst entfernt.
    29: '',
    64: '{{ .Params.text1 | safeHTML }}',
    67: '{{ .Params.stadt }}',
    # Zeile 85: auskommentierter Bewertungsblock (SELECT auf bewertungen)
    # samt Stadtfoto-Einbindung. Gibt seit Jahren nichts aus -> entfaellt.
    85: '',
    149: '{{ .Params.text2 | safeHTML }}',
    153: '{{ if eq .Params.stadt "Berlin" }}',
    179: '{{ end }}',
    183: '{{ if eq .Params.stadt "" }}',
    263: '{{ end }}',
}

TOPIC_MAP = {
    6: '',                                      # $title_short = explode(...)
    9: '{{ index (split .Title "|") 0 }}',      # H1 = Titel bis zum ersten |
    46: '{{ .Params.text1 | safeHTML }}',
    67: '',                                     # toter Bewertungsblock
    115: '{{ .Params.text2 | safeHTML }}',
}


def convert(relpath, mapping, what):
    parts = tokenize(relpath)
    out, unknown = [], []
    for p in parts:
        if p['kind'] == 'html':
            out.append(p['text'])
        else:
            if p['line'] not in mapping:
                unknown.append((p['line'], ' '.join(p['text'].split())[:90]))
            else:
                out.append(mapping[p['line']])
    if unknown:
        print('FEHLER: unbekannte PHP-Abschnitte in %s:' % relpath)
        for line, txt in unknown:
            print('   Zeile %s: %s' % (line, txt))
        sys.exit(1)
    body = ''.join(out)
    print('  %-32s %2d Abschnitte -> %6d B  %s' % (relpath, len(parts), len(body), what))
    return body


def main():
    print('Layouts aus PHP-Quelle uebersetzt:')

    city = convert('staedte/pc-hilfe.php', CITY_MAP, 'layouts/_partials/pc-hilfe.html')
    write('layouts/_partials/pc-hilfe.html', city)
    # Staedteseiten und die Uebersicht /pc-hilfe teilen denselben Rumpf;
    # die Unterschiede haengen nur an .Params.stadt.
    write('layouts/pc-hilfe/page.html',
          '{{ define "main" }}{{ partial "pc-hilfe.html" . }}{{ end }}\n')
    write('layouts/pc-hilfe/section.html',
          '{{ define "main" }}{{ partial "pc-hilfe.html" . }}{{ end }}\n')

    topic = convert('themen/hilfethemen.php', TOPIC_MAP, 'layouts/thema/page.html')
    write('layouts/thema/page.html',
          '{{ define "main" }}' + topic + '{{ end }}')


if __name__ == '__main__':
    main()
