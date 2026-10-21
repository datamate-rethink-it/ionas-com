# ionas.com – statische Seite mit Hugo

Ersetzt ionas.com vollständig: den alten PHP-Teil **und** das WordPress
unter `/wissen`. Das WordPress kann nach dem Umstieg abgeschaltet werden.

Stand: 21.10.2026 · Hugo 0.168.0 (extended) · Quellen: `ionas-com.tar.gz`
und die WordPress-REST-API der Live-Installation

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

Alle 96 Seiten des PHP-Teils kommen Byte für Byte so heraus wie bisher –
bis auf zwei bewusste, systematische Abweichungen, die der Vergleich
normalisiert:

| Abweichung | Grund |
|---|---|
| `&` und `'` in Titel/Description sind jetzt `&amp;` / `&#39;` | Hugo kodiert korrekt; das alte PHP gab sie roh aus (formal invalides HTML, identische Darstellung) |
| HTML-Kommentare im `<head>` fehlen im Ergebnis | Go's `html/template` entfernt sie beim Rendern. Sie stehen weiterhin in `layouts/baseof.html` – nur nicht mehr im ausgelieferten HTML |

Für die 150 Wissensartikel ist Byte-Gleichheit **nicht** das Ziel: der
WordPress-Kopf enthielt Emoji-Skripte, oEmbed- und wp-json-Verweise,
XML-RPC-Pingback und Gutenberg-CSS, die bewusst nicht mitgekommen sind.
Geprüft wird, was für Besucher und Suchmaschinen zählt:

```
$ _build/verify_wissen.py
Wissensartikel geprüft: 150
  Artikeltext identisch        150 / 150
  title                       150 / 150
  description                 150 / 150
  canonical                   150 / 150
  robots                      150 / 150
  Kommentare vollständig       150 / 150  (280 Kommentare)
  Vor/Zurück-Verweise          150 / 150
  Schlagwort-Verweise          150 / 150
  Teaser der Übersicht         150 / 150
keine Abweichungen
```

---

## Struktur

```
hugo.toml                   Konfiguration (kommentiert)
content/                    316 Seiten – nur Inhalt, kein Layout
  _index.html               Startseite
  <slug>.html               21 einfache Seiten (Leistungen, Impressum, …)
  pc-hilfe/_index.html      Übersicht /pc-hilfe
  pc-hilfe/<stadt>.html     56 Städte-Landingpages
  <thema>.html              19 Hilfethemen (type: thema)
  wissen/_index.html        Artikelübersicht /wissen/
  wissen/<slug>.html        150 Wissensartikel
  wissen/suche.html         Suchseite
  wissen-archiv/<jahr-monat>.html   68 Monatsarchive
layouts/                    1095 Zeilen – das gesamte Seitengerüst
  baseof.html               Rahmen, wählt zwischen den beiden <head>-Varianten
  _partials/kopf-ionas.html     <head> des PHP-Teils
  _partials/kopf-wissen.html    <head> der Wissensartikel (SEO-Metadaten)
  _partials/site-header.html    Navigation
  _partials/site-footer.html    Footer
  _partials/home-seo.html       SEO-Textblock, nur auf der Startseite
  _partials/pc-hilfe.html       Städte-Template (aus staedte/pc-hilfe.php)
  _partials/wissen-sidebar.html     Seitenleiste der Artikel
  _partials/wissen-liste.html       ein Eintrag der Artikellisten
  _partials/wissen-kommentare.html  die übernommenen Kommentare
  _partials/wissen-schema.html      JSON-LD, Form wie bisher von Yoast
  thema/page.html               Hilfethemen-Template (aus themen/hilfethemen.php)
  wissen/page.html              ein Wissensartikel
  wissen/section.html           Artikelübersicht, 100 je Seite
  wissen/section.wissenfeed.xml     /wissen/feed.xml
  wissen/section.wissen*sitemap*.xml  die drei Sitemaps aus /wissen/
  wissen-archiv/page.html       Monatsarchiv
  term.html                     Schlagwortseite /wissen/tag/<slug>/
  home.mainsitemap.xml          erzeugt sitemap/main.xml
  404.html
data/sitemap_extra.yaml     Sitemap-Einträge, die keine Seiten sind (PDFs, /agb)
data/kommentare.yaml        280 übernommene Kommentare, nach Artikel gruppiert
data/tagnamen.yaml          Anzeigenamen der 333 benutzten Schlagwörter
webroot/                    124 MB, wird unverändert unter / ausgeliefert
  wissen/wp-content/uploads/    die Artikelbilder unter ihren alten Adressen
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
npx pagefind --site public                  # Suchindex für /wissen/suche/
rsync -a --delete public/ server:/var/www/ionas/
```

Der Pagefind-Lauf ist nur für die Suche nötig. Ohne ihn steht die Seite
`/wissen/suche/` da und meldet, dass die Suche nicht verfügbar ist – alles
andere funktioniert.

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

## Die Wissensartikel

150 Beiträge aus den Jahren 2014 bis 2026, geholt über die REST-API der
WordPress-Installation. Der **Artikeltext** stammt aus den gerenderten
Seiten, nicht aus der API: nur dort steht die `<span id="more-NNN">`-Marke,
an der WordPress den Teaser für die Übersicht abschneidet.

Mitgekommen sind auch:

- **280 Kommentare** auf 38 Artikeln (2015–2019, seit dann keine neuen) als
  reines HTML unter dem Artikel. Kein Formular mehr – eine statische Seite
  nimmt keine Eingaben an.
- **333 Schlagwörter** mit ihren Seiten unter `/wissen/tag/<slug>/`, auf
  `noindex, follow` – genau wie Yoast sie behandelt hat (sie standen nie in
  der Sitemap). 47 Schlagwörter ohne Beitrag sind weggefallen.
- **68 Monatsarchive** unter `/wissen/<jahr>/<monat>/`, ebenfalls noindex.
- Der **RSS-Feed** unter `/wissen/feed/` (im Footer jeder Seite verlinkt).
- Die **drei Yoast-Sitemaps** `/wissen/sitemap_index.xml`,
  `post-sitemap.xml` und `page-sitemap.xml`. Der Index ist in der Search
  Console eingetragen und bleibt deshalb unter derselben Adresse.
- Das **JSON-LD** in Yoasts Form (Organization, WebSite, ImageObject,
  WebPage, BreadcrumbList, Article, Person), erzeugt in
  `_partials/wissen-schema.html` statt 150 Mal gespeichert.
- Die **Bilder** bleiben unter `/wissen/wp-content/uploads/…`. Unschön, aber
  so brechen keine Verweise aus Google Bilder oder von fremden Seiten.

### Drei Plugins ersetzt

| vorher | jetzt |
|---|---|
| simple-lightbox, 217 KB, neun Skriptdateien, jQuery | `webroot/static/js/lightbox.js`, 2 KB Vanilla-JS auf `<dialog>`. Greift dieselbe Auszeichnung ab (`<a href="bild.jpg"><img>`), kein Artikel musste angefasst werden |
| WordPress-Suche (`?s=`) | Pagefind unter `/wissen/suche/`, Index aus 150 Artikeln. Die Seitenleiste zeigt dorthin |
| Yoast SEO | `_partials/kopf-wissen.html` und `_partials/wissen-schema.html` |

### Abweichungen im Erscheinungsbild

- Die **Schriftgrößen der Schlagwortwolke** folgen der dokumentierten
  linearen WordPress-Formel (8–22 pt). Das Widget benutzte eine nicht
  nachvollziehbare Skalierung; die Abstufung wirkt gleich, einzelne
  Begriffe sind ein bis zwei Punkt größer oder kleiner.
- Der **viewport**-Meta stand im WordPress viermal im Kopf, zuletzt mit
  `maximum-scale=1.0, user-scalable=no`. Das verhindert Zoomen auf dem
  Handy. Jetzt steht dort nur noch die zoombare Variante wie im übrigen
  Teil der Seite.
- Hugo schreibt `"` als `&#34;` und `+` als `&#43;`, Yoast schrieb `&quot;`
  bzw. `+`. Gleiche Darstellung; im `<title>` lässt sich Gos Maskierung
  nicht abschalten.

### Einen Artikel schreiben

Eine Datei in `content/wissen/` anlegen:

```markdown
---
title: "Überschrift des Artikels"
date: 2026-11-02
url: "/wissen/mein-neuer-artikel/"
wissen: true
autor: "Christoph Dyllick-Brenzinger"
beschreibung: "Ein Satz für Suchergebnis und Vorschau."
canonical_url: "https://www.ionas.com/wissen/mein-neuer-artikel/"
tags: ["backup", "windows"]
---

Erster Absatz, der als Teaser in der Übersicht erscheint.

<!--more-->

Der Rest des Artikels.
```

Markdown geht hier, anders als bei den übernommenen Artikeln: die liegen als
HTML vor, weil sie wortgleich aus WordPress kommen. Beides darf im selben
Verzeichnis liegen.

Die übernommenen Artikel haben ein Feld `teaser` mit dem Übersichtstext.
Neue Artikel brauchen es nicht – ohne `teaser` greift Hugos `.Summary`, also
der Text vor `<!--more-->`. Der Grund für das Feld: WordPress hängt den
„(mehr …)"-Verweis bei 122 Artikeln als eigenen Absatz an, bei 28 mitten in
den letzten Absatz. Aus dem Volltext ist das nicht zu rekonstruieren.

Schlagwörter stehen als Slug in der Frontmatter; der Anzeigename kommt aus
`data/tagnamen.yaml`. Ein neues Schlagwort dort ergänzen, sonst fehlt es in
der Wolke und auf der Seitenleiste.

### Das WordPress abschalten

Nach dem Umstieg wird unter `/wissen` nichts mehr dynamisch ausgeliefert –
`deploy/Caddyfile` enthält keinen Proxy mehr dorthin. Damit entfallen
WordPress 5.9.2 (über vier Jahre ohne Updates), die neun Plugins, die
MySQL-Datenbank und der Login unter `/wissen/wp-admin/`.

Vorher sichern, weil es danach keine Oberfläche mehr gibt, über die man
herankommt:

```bash
mysqldump wp_ionas_com | gzip > wp_ionas_com_$(date +%F).sql.gz
tar czf wissen-wp-content_$(date +%F).tar.gz wissen/wp-content
```

Die Artikel selbst liegen danach als Dateien in `content/wissen/` und
brauchen die Datenbank nicht mehr.

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

Zusätzlich fallen **419 Dateien mit 68 MB** weg, auf die keine einzige
ausgelieferte Seite verweist – weder per `src`/`href`/`srcset` noch über
`url()` in einem Stylesheet noch aus einer Sitemap:

| | |
|---|---|
| 179 | nie in einem Artikel verwendete Uploads |
| 176 | Bilder unter `/static/img`, darunter 3,2 MB GIMP-Quelldateien (`.xcf`) |
| 15 + 7 | Skripte und Stylesheets, teils mit Namen wie `own_old.css`, `style_veraltet_alt.css` |
| 19 + 10 + 10 | ungenutzte Dateien unter `/images`, `/ionas-neu`, `/senderlogos` |
| 3 | PDFs, darunter eine ältere AGB-Fassung |

Die Liste steht in `_build/nicht-ausliefern.txt` und wird von
`_build/verwaiste_assets.py --schreiben` gegen ein fertig gebautes `public/`
erzeugt; `gen_static.py` und `gen_wissen.py` lesen sie.

Eine pauschale Regel wäre hier die falsche Wahl gewesen: unter
`static/js/parallax/` liegen 20 MB Demobilder der Library – aber eines davon
bindet die Startseite tatsächlich ein. Deshalb entscheidet der tatsächliche
Verweis, nicht der Ordner.

Damit sinkt das Auszuliefernde von rund 240 MB auf **124 MB**, davon
105 MB Artikelbilder.

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

Dazu drei Weiterleitungen aus den Wissensartikeln: `/drucker-druckt-nicht/`,
`/datensicherung-mit-windows-bordmitteln/` und
`/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/`.
Drei Artikel verlinken aufeinander ohne das `/wissen`-Präfix; diese Adressen
liefern auch im WordPress 404. Die Weiterleitung repariert das, ohne die
Artikeltexte anzufassen.

Hugo legt für die Aliase zusätzlich `meta-refresh`-Seiten ab. Die 301 greift
zuerst; die Dateien sind der Rückfall, falls die Seite mal ohne diese
Konfiguration ausgeliefert wird.

`/wissen/feed/` wird intern auf die von Hugo erzeugte `/wissen/feed.xml`
umgeschrieben, damit die im Footer verlinkte Adresse gleich bleibt.

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

Dasselbe gilt für zwei Hintergrundbilder, die das WordPress-Theme in seiner
`style.css` unter `/wissen/startup/common-files/icons/menu-icon*@2x.png`
sucht. Die Dateien liegen tatsächlich unter `/images/`; im WordPress fehlen
sie seit immer. Nicht korrigiert, weil dafür das Theme-Stylesheet geändert
werden müsste und die Symbole vom Haupt-CSS ohnehin gestellt werden.

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

**Bilder neu kodieren.** `webroot/` ist mit 124 MB weiter vom Bildbestand
der Artikel bestimmt. Ungenutzte Zwischengrößen und verwaiste Dateien sind
weg; was bleibt, sind benutzte Bilder, von denen einige mehrere Megabyte
groß sind und im Artikel auf 450 px angezeigt werden. Eine Runde `cwebp`
oder ein Resize würde das deutlich drücken – ändert aber ausgelieferte
Dateien und ist deshalb kein Aufräumen mehr, sondern eine Entscheidung.

**Die Suchoberfläche einmal anklicken.** Der Pagefind-Index baut (150
Seiten, 16 027 Wörter) und `pagefind-ui.js` setzt `window.PagefindUI` mit
allen neun Übersetzungsschlüsseln, die `suche.js` verwendet – das ist
geprüft. Die Oberfläche selbst wurde nicht im Browser bedient; hier stand
keine Browser-Verbindung zur Verfügung. Nach dem Deploy einmal
`/wissen/suche/` öffnen und einen Begriff eintippen.

## Migration nachvollziehen oder wiederholen

`_build/` enthält das vollständige Werkzeug. Es ist nicht nötig, um die Seite
zu bauen – nur um die Umwandlung zu wiederholen oder zu prüfen:

Der Referenz-Snapshot des alten PHP-Stands liegt mit im Repo
(`_build/reference/`, 118 Seiten, 2,9 MB). `verify.py` braucht deshalb weder
PHP noch den Tarball:

```bash
python3 _build/verify.py          # PHP-Teil, Seite für Seite
python3 _build/verify_wissen.py   # Wissensartikel
python3 _build/linkcheck.py       # alle seiteninternen Verweise
```

`linkcheck.py` kennt die Adressen, die erst der Webserver auflöst (`/agb`,
`/wissen/feed/`, die Weiterleitungen) und die zwölf Verweise, die schon vor
der Migration ins Leere liefen. Es meldet nur, was **neu** kaputt ist.

Die Umwandlung selbst wiederholen (braucht den entpackten Quellbaum):

```bash
export IONAS_SRC=/pfad/zum/entpackten/website
_build/build.sh      # erzeugt hugo.toml, layouts/, content/, webroot/, data/
hugo --gc
python3 _build/verify.py
```

Ein Neulauf von `build.sh` erzeugt bit-identisch denselben Stand – geprüft
über `git status` nach einem `rm -rf layouts content webroot data`.

Die Reihenfolge ist: `gen_layouts.py` (Gerüst aus dem Referenz-Render),
`gen_tpl.py` (Städte- und Themen-Template aus der PHP-Quelle),
`gen_content.py` (96 Seiten), `gen_static.py` (Assets + Sitemap),
`gen_wissen.py` (150 Artikel, Kommentare, Schlagwörter, Archive),
`gen_deploy.py` (Caddy/nginx).

Die handgeschriebenen Templates des Wissensbereichs liegen als lesbare
Dateien in `_build/templates/`, die Skripte in `_build/assets/`;
`gen_wissen.py` kopiert sie nach `layouts/` bzw. `webroot/`. Die
WordPress-Daten liegen als JSON in `_build/wp/` (Beiträge, Kommentare,
Schlagwörter, Teaser) und die gerenderten Vergleichsseiten in
`_build/reference-wissen/`.

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

## Zum alten Quellbaum

`functions.php` enthält MySQL- und SMTP-Zugangsdaten im Klartext und
`storage/contracts/` 60 Kundenvertrags-PDFs. Beides ist im neuen Webroot
nicht enthalten und wird mit Seite und Datenbank abgelöst – erledigt sich
also mit dem Umstieg.
