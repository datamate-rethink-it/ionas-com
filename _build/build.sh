#!/usr/bin/env bash
# Erzeugt das komplette Hugo-Projekt neu aus dem alten PHP-Quellbaum.
# Einmal-Migrationswerkzeug - nach dem Umstieg nicht mehr noetig.
set -euo pipefail

: "${IONAS_SRC:?Pfad zum entpackten website/-Verzeichnis setzen}"
: "${IONAS_REF:?Pfad zum Referenz-Snapshot setzen}"
export IONAS_PRJ="${IONAS_PRJ:-$(cd "$(dirname "$0")/.." && pwd)}"

cd "$(dirname "$0")"
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
echo
echo "fertig: $IONAS_PRJ"
