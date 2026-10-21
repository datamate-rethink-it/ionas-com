# ionas.com – statische Seite mit Hugo

Ersetzt den alten PHP-Teil von ionas.com (alles **außer** `/wissen`).
`/wissen` bleibt unverändert das bestehende WordPress und wird vom Webserver
durchgereicht.

Stand: 21.10.2026 · Hugo 0.168.0 (extended) · Quelle: `ionas-com.tar.gz`

---

## Der Nachweis

Der alte Code wurde vollständig gerendert (alle 118 Routen des
`switch`-Routers in `index.php`) und dieser Snapshot stichprobenartig gegen
die Live-Seite geprüft: **byte-identisch**. Er dient als Referenz, gegen die
die Hugo-Ausgabe geprüft wird:

```
$ _build/verify.py
identisch: 96    abweichend: 0    fehlend: 0    (von 96 Seiten)
```

Alle 96 Seiten kommen Byte für Byte so heraus wie bisher – bis auf zwei
bewusste, systematische Abweichungen, die der Vergleich normalisiert:

| Abweichung | Grund |
|---|---|
| `&` und `'` in Titel/Description sind jetzt `&amp;` / `&#39;` | Hugo kodiert korrekt; das alte PHP gab sie roh aus (formal invalides HTML, identische Darstellung) |
| HTML-Kommentare im `<head>` fehlen im Ergebnis | Go's `html/template` entfernt sie beim Rendern. Sie stehen weiterhin in `layouts/baseof.html` – nur nicht mehr im ausgelieferten HTML |

---

## Struktur

```
hugo.toml                   Konfiguration (kommentiert)
content/                    96 Seiten – nur Inhalt, kein Layout
  _index.html               Startseite
  <slug>.html               21 einfache Seiten (Leistungen, Impressum, …)
  pc-hilfe/_index.html      Übersicht /pc-hilfe
  pc-hilfe/<stadt>.html     56 Städte-Landingpages
  <thema>.html              19 Hilfethemen (type: thema)
layouts/                    602 Zeilen – das gesamte Seitengerüst
  baseof.html               <head>, Rahmen
  _partials/site-header.html    Navigation
  _partials/site-footer.html    Footer
  _partials/home-seo.html       SEO-Textblock, nur auf der Startseite
  _partials/pc-hilfe.html       Städte-Template (aus staedte/pc-hilfe.php)
  thema/page.html               Hilfethemen-Template (aus themen/hilfethemen.php)
  home.mainsitemap.xml          erzeugt sitemap/main.xml
  404.html
data/sitemap_extra.yaml     Sitemap-Einträge, die keine Seiten sind (PDFs, /agb)
webroot/                    41 MB, wird unverändert unter / ausgeliefert
deploy/Caddyfile            fertige Caddy-Konfiguration
deploy/nginx-ionas.conf     Alternative für den bestehenden nginx
_build/                     Einmal-Migrationswerkzeug, nach dem Umstieg löschbar
```

`webroot/` heißt absichtlich nicht `static/` (Hugos Standard), weil die Seite
selbst einen Pfad `/static/` für CSS und JS benutzt – zwei Bedeutungen von
„static" im selben Projekt wären verwirrend. Gesetzt über `staticDir` in
`hugo.toml`.

## Bauen und ausrollen

```bash
hugo --gc                                   # erzeugt public/
rsync -a --delete public/ server:/var/www/ionas/
```

Kein `--minify`: das würde die Byte-Gleichheit mit dem alten Stand aufgeben.
`[minify] disableHTML = true` in `hugo.toml` ist die Bremse, falls es doch
mal jemand setzt.

Lokal ansehen:

```bash
hugo server
```

Vor dem ersten Ausrollen `caddy validate --config deploy/Caddyfile` laufen
lassen – die Datei ist hier nie von Caddy selbst geprüft worden.

## Etwas ändern

**Text auf einer normalen Seite** → die entsprechende Datei in `content/`.
Reines HTML, kein Markdown.

**Telefonnummer, Navigation, Footer, Impressumslink** → `layouts/_partials/`.
Einmal ändern, wirkt auf allen 96 Seiten. Das war vorher der eigentliche
Schmerz: `header.php`/`footer.php` waren zwar schon geteilt, aber die
Städte- und Themenseiten hatten ihre Texte in zwei `switch`-Blöcken von
316 KB bzw. 135 KB liegen.

**Eine Stadt** → `content/pc-hilfe/<stadt>.html`. Die beiden Textblöcke
stehen als YAML-Literalblöcke `text1:` und `text2:` in der Frontmatter, weil
das Layout zwischen ihnen die gemeinsame Preistabelle einschiebt. `stadt:`
steuert Breadcrumb und Überschriften, `canonical:` die URL im
`<link rel="canonical">`.

**Eine Stadt dazu** → Datei nach dem Muster einer bestehenden anlegen,
`url:` und `canonical:` setzen. Sonst nichts; das Layout greift automatisch.

**Sitemap** → wird aus `sitemap_loc`/`sitemap_priority`/`sitemap_changefreq`/
`sitemap_lastmod` der Frontmatter erzeugt, plus `data/sitemap_extra.yaml` für
die PDFs. `sitemap.xml` selbst bleibt ein statischer Index in `webroot/`,
weil er auch auf `wissen/sitemap_index.xml` zeigt.

## Was bewusst nicht mitgekommen ist

11 der 118 Routen sind entfallen. Keine davon ist verlinkt oder steht in der
Sitemap; die Formularseiten laufen **schon in der Produktion** in einen
PHP-Fehler und liefern eine leere Seite:

| Route | Grund |
|---|---|
| `/vertragsabschluss`, `/kontoaenderung` | Formulare mit DB- und Mailversand. Die Hotline ist zum 01.04.2020 eingestellt (steht so auf `/preise`), die Formulare liefern live 9,7 KB nackte Seite |
| `/portscan`, `/lets-encrypt`, `/test` | interne Werkzeuge, brauchen PHP |
| `/weihnachten`, `/computerhilfe-fuer-eltern` | `pages/weihnachten2015.php` fehlt seit Jahren; liefert live eine leere Seite. **War in der Sitemap** – dort jetzt entfernt |
| `/kontoaenderung2`, `/vertragsabschluss2`, `/laptop-hilfe`, `/pc-hotline` | lieferten schon vorher absichtlich die 404-Seite |

Zusätzlich an totem Code entfernt:

- **Stadtfotos** (`staedte/fotos/`, 15 MB) – nur aus einem `/* */`-Block in
  `pc-hilfe.php` verlinkt, erschienen nie im HTML
- **Bewertungsblock** mit `aggregateRating`-Schema auf Städte- und
  Themenseiten – ebenfalls auskommentiert, seit Jahren ohne Ausgabe
- **Parallax-Demobilder** (`static/js/parallax/*.jpg|png`, 20 MB) – Beispiel­
  material der Library, nur das `.js` wird eingebunden
- `demo/`, `storage/`, `phpmailer/`, `cronjob/`, `external/`, die
  `*.php`-Generatoren in `sitemap/`

Damit sinkt das Auszuliefernde von rund 100 MB auf **41 MB**.

## Weiterleitungen (in `deploy/Caddyfile`)

11 echte 301 statt der bisherigen doppelt ausgelieferten Inhalte:

- 10 ASCII-Schreibweisen der Umlaut-Landingpages
  (`/pc-hilfe/muenchen` → `/pc-hilfe/münchen` usw.). Die `canonical`-Tags
  zeigten schon vorher auf die Umlaut-Variante, der Inhalt wurde aber unter
  beiden URLs mit 200 ausgeliefert.
- `/rescue-stick` → `/usb-stick`
- `/Datenschutz` → `/datenschutz` (so ist die URL in der
  Datenschutzerklärung abgedruckt; der Text bleibt unangetastet)
- neu: `ionas.com` → `www.ionas.com`. Bisher lieferten **beide** Hosts 200
  ohne Weiterleitung, obwohl alle `canonical` auf `www` zeigen.

Hugo legt für die Aliase zusätzlich `meta-refresh`-Seiten ab. Die 301 greift
zuerst; die Dateien sind der Rückfall, falls die Seite mal ohne diese
Konfiguration ausgeliefert wird.

`/agb` liefert weiterhin `downloads/AGB-ionas.pdf`. Das war eine
Rewrite-Regel im nginx-vhost und stand **nicht** im Tarball – leicht zu
übersehen, die URL steht im Footer jeder Seite und in der Sitemap. Nebenbei
korrigiert: nginx liefert das PDF bisher als `text/html` aus.

## Was weiterhin kaputt ist (war es vorher auch)

Nicht angefasst, weil die Dateien fehlen und nur du entscheiden kannst, ob
sie aus einem Backup zurückkommen oder die Links weg sollen:

| fehlende Datei | verlinkt von |
|---|---|
| `/downloads/CV_RalfDyllick-Brenzinger.pdf` | `/presse` |
| `/downloads/CV_ChristophDyllick-Brenzinger.pdf` | `/presse` |
| `/static/presse/1510_Gewinner Mainzer Wirtschaftspreis-2015.pdf` | `/presse` |

Alle drei liefern live 404 und standen in der Sitemap – dort jetzt entfernt.

Harmlos, aber vorhanden: `bootstrap.min.css` sucht vier
`glyphicons-halflings-regular.*`-Dateien, von denen nur die `.woff`
existiert, und `startupframework.css` sucht
`/startup/common-files/img/header/img-3.jpg`. Beides fehlt seit immer;
Browser ignorieren es still.

## Naheliegende nächste Schritte

**Google Fonts lokal hosten.** `layouts/baseof.html` lädt
`//fonts.googleapis.com/css?family=Open+Sans+Condensed:300,700` – nach dem
LG-München-Urteil ein DSGVO-Risiko. Zwei Dateien nach `webroot/static/fonts/`
legen, `@font-face` in `webroot/static/css/ionas.css` ergänzen, die
`<link>`-Zeile in `baseof.html` entfernen. Bewusst nicht gemacht, damit der
Byte-Vergleich oben sauber bleibt.

**Toten Code im `<head>` aufräumen.** `baseof.html` enthält noch
`rel="author"`/`rel="publisher"` auf `plus.google.com` (Google+ ist seit 2019
abgeschaltet) und eine `alexaVerifyID` (Alexa seit 2022 eingestellt).

**`/wissen`.** Das ist der verbleibende Risikoträger: WordPress 5.9.2 von
März 2022, über vier Jahre ohne Updates, 167 MB Uploads, acht neue Artikel
pro Jahr. Der statische PHP-Teil senkt die Angriffsfläche nur um den
kleineren Teil.

## Migration nachvollziehen oder wiederholen

`_build/` enthält das vollständige Werkzeug. Es ist nicht nötig, um die Seite
zu bauen – nur um die Umwandlung zu wiederholen oder zu prüfen:

```bash
export IONAS_SRC=/pfad/zum/entpackten/website
export IONAS_REF=/pfad/zum/referenz-snapshot
_build/build.sh      # erzeugt hugo.toml, layouts/, content/, webroot/, data/
hugo --gc
_build/verify.py     # vergleicht public/ Seite für Seite mit dem Referenz-Snapshot
```

Die Reihenfolge ist: `gen_layouts.py` (Gerüst aus dem Referenz-Render),
`gen_tpl.py` (Städte- und Themen-Template aus der PHP-Quelle),
`gen_content.py` (96 Seiten), `gen_static.py` (Assets + Sitemap),
`gen_deploy.py` (Caddy/nginx).

`gen_tpl.py` lässt PHP selbst tokenisieren (`tok.php`), statt mit Regexen
HTML von PHP zu trennen: in `pc-hilfe.php` überspannt ein `/* */`-Kommentar
mehrere `<?php ?>`-Blöcke, was per Regex nicht sicher zu erkennen ist. Jeder
PHP-Abschnitt ist dort einzeln auf sein Hugo-Pendant abgebildet; ein
unbekannter Abschnitt bricht den Lauf ab, statt stillschweigend Inhalt zu
verschlucken.

Den Referenz-Snapshot neu erzeugen:

```bash
cd /pfad/zum/entpackten/website && php -S 127.0.0.1:8899 index.php &
grep -oP "case\s+'\K[^']+" index.php | sort -u | while read r; do
  out="$IONAS_REF/${r#/}"; [ "$r" = startseite ] && out="$IONAS_REF"
  mkdir -p "$out"
  curl -sG --data-urlencode "p=$r" http://127.0.0.1:8899/ > "$out/index.html"
done
```

Eine Ausnahme: `/preise` zieht zwei Kundenstimmen per `SELECT` aus der
MySQL-Tabelle `bewertungen` und ist die einzige Seite, die ohne Datenbank in
einen Fatal Error läuft. Deren Referenz stammt deshalb von der Live-Seite;
die beiden Kundenstimmen stehen jetzt als HTML in `content/preise.html`.

---

## Noch zu tun, unabhängig von dieser Migration

1. **`functions.php` im alten Quellbaum enthält Klartext-Zugangsdaten**:
   MySQL-Credentials der WordPress-Datenbank und das SMTP-Passwort von
   `noreply@datamate.de`, dazu eine auskommentierte Root-Verbindung zu
   `37.148.137.58`. Passwörter rotieren, das Tarball nicht weitergeben.
2. **`storage/contracts/` enthält 60 Kundenvertrags-PDFs** mit Klarnamen
   (Muster `200107_NachnameVorname_106506.pdf`), dazu `storage/sepa-updates/`.
   Prüfen, ob die öffentlich abrufbar sind:
   `curl -sI https://www.ionas.com/storage/contracts/<datei>.pdf | head -1`
   Ein `200` wäre ein meldepflichtiger Datenschutzvorfall. Im neuen Webroot
   sind diese Dateien nicht enthalten.
