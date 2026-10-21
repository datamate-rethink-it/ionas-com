#!/usr/bin/env bash
# Erzeugt das komplette Hugo-Projekt neu aus dem alten PHP-Quellbaum.
# Einmal-Migrationswerkzeug - nach dem Umstieg nicht mehr noetig.
set -euo pipefail

: "${IONAS_SRC:?Pfad zum entpackten website/-Verzeichnis setzen}"
export IONAS_PRJ="${IONAS_PRJ:-$(cd "$(dirname "$0")/.." && pwd)}"

cd "$(dirname "$0")"

# layouts/ enthaelt seit dem Aufloesen von _build/templates/ auch
# handgeschriebene Dateien, die hier NICHT erzeugt werden - die Templates
# des Wissensbereichs. Fehlen sie, baut Hugo eine kaputte Seite, ohne sich
# zu beschweren. Deshalb hier der Riegel.
fehlend=""
for f in \
    layouts/wissen/page.html \
    layouts/wissen/section.html \
    layouts/wissen-archiv/page.html \
    layouts/term.html \
    layouts/_partials/kopf-wissen.html \
    layouts/_partials/wissen-sidebar.html \
    layouts/_partials/wissen-liste.html \
    layouts/_partials/wissen-kommentare.html \
    layouts/_partials/wissen-schema.html
do
    [ -f "$IONAS_PRJ/$f" ] || fehlend="$fehlend  $f\n"
done
if [ -n "$fehlend" ]; then
    printf 'Diese handgeschriebenen Layouts fehlen:\n%b' "$fehlend"
    echo "Sie werden hier nicht erzeugt. Wiederherstellen mit:"
    echo "    git checkout -- layouts"
    exit 1
fi

echo "== Routentabelle =="
php -d error_reporting=0 ./router-head.php startseite >/dev/null   # Rauchtest
echo "   routes.json: $(python3 -c 'import json;print(len(json.load(open("routes.json"))))') Routen"
echo "== Layouts =="
python3 gen_layouts.py
echo "== Templates aus PHP =="
python3 gen_tpl.py
echo "== Inhalte =="
python3 gen_content.py
echo "== Assets + Sitemap =="
python3 gen_static.py
echo "== Wissensartikel =="
python3 gen_wissen.py
echo
echo "fertig: $IONAS_PRJ"

echo
echo "Nächste Schritte:"
echo "  hugo --gc                   # erzeugt public/"
echo "  npx pagefind --site public  # Suchindex für /wissen/suche/"
echo "  python3 _build/verify.py && python3 _build/verify_wissen.py"
