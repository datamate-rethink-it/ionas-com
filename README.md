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
webroot/                    124 MB übernommener Dateibestand, unter /
  wissen/wp-content/uploads/    die Artikelbilder unter ihren alten Adressen
webroot-eigen/              selbst geschriebene Dateien, ebenfalls unter /
  static/js/lightbox.js         Bildvergrößerung (ersetzt simple-lightbox)
  static/js/suche.js            bindet Pagefind auf /wissen/suche/ ein
  static/css/lightbox.css
Dockerfile                  Caddy + die gebaute Seite, zwei Schichten
deploy/Caddyfile.container  die Regeln im Image
deploy/nginx-vhost.conf     der vhost für das native nginx davor
deploy/docker-compose.yml   für /opt/ionas.com/ auf dem Server
.github/workflows/build.yml prüft jeden Push, veröffentlicht bei Tag
_build/                     Einmal-Migrationswerkzeug, nach dem Umstieg löschbar
```

`webroot/` heißt absichtlich nicht `static/` (Hugos Standard), weil die Seite
selbst einen Pfad `/static/` für CSS und JS benutzt – zwei Bedeutungen von
„static" im selben Projekt wären verwirrend.

Es sind zwei Verzeichnisse, weil `_build/gen_static.py` `webroot/` jedes Mal
neu aus dem alten Quellbaum erzeugt. Was dort hineingelegt wird, ist beim
nächsten Lauf weg. Selbst geschriebene Dateien gehören deshalb nach
`webroot-eigen/`; Hugo mischt beide über `staticDir = ['webroot',
'webroot-eigen']`.

## Bauen und ausrollen

Die Seite wird als Docker-Image ausgeliefert: Caddy mit dem fertig gebauten
HTML. Davor steht das nativ installierte nginx des Servers.

Diese Teilung hat einen Grund. Der fragile Teil dieser Migration sind nicht
die Dateien, sondern die **Ausliefer-Regeln**: 16 Weiterleitungen, der
`/agb`-Rewrite auf die AGB-PDF, der `/wissen/feed/`-Rewrite, `try_files` für
die extensionslosen URLs, der 404-Handler. Die `/agb`-Regel stand bisher
*nur* im nginx-vhost und nicht im Quellbaum – und sie hängt im Footer jeder
einzelnen Seite. Im Image sind diese Regeln mit dem Inhalt zusammen
versioniert und können nicht mehr durch einen unbeteiligten
`nginx -s reload` verschwinden.

Dazu: `docker compose up -d` tauscht die Seite in einem Zug. Ein `rsync` von
148 MB ist nicht atomar – mitten im Lauf verweist eine Seite auf ein Bild,
das noch nicht da ist. Und ein Rückschritt ist ein Tag.

```
Browser ──► nginx (nativ)        TLS, ionas.com ──► www.ionas.com
                 │               deploy/nginx-vhost.conf
                 ▼
            Container :8081      alles Übrige: Weiterleitungen, /agb,
            Caddy + HTML         Feed, try_files, 404, Cache-Header
                                 deploy/Caddyfile.container
```

### Lokal

```bash
hugo --gc                        # erzeugt public/
npx pagefind --site public       # Suchindex für /wissen/suche/
hugo server                      # ansehen
```

Oder gleich als Image, so wie es auf dem Server läuft:

```bash
docker build -t ionas-com:dev .
docker run --rm -p 127.0.0.1:8099:80 ionas-com:dev
```

Der Build ist in sich geschlossen: ein frischer Clone genügt, es braucht
weder den alten PHP-Quellbaum noch Node. Hugo und Pagefind lädt das
Dockerfile als Binärdateien, die Versionen stehen dort als `ARG`.

Kein `--minify`: das gäbe die Byte-Gleichheit auf, die `_build/verify.py`
nachweist. `[minify] disableHTML = true` in `hugo.toml` ist die Bremse,
falls es doch jemand setzt.

### Veröffentlichen

```bash
git tag 2026-10-21
git push --tags
```

[`.github/workflows/build.yml`](.github/workflows/build.yml) prüft bei jedem
Push die Ausgabe (`verify.py`, `verify_wissen.py`, `linkcheck.py`, plus
`caddy validate`) und veröffentlicht bei einem Tag das Image nach
`ghcr.io/datamate-rethink-it/ionas-com`. Die Werkzeugversionen liest der
Workflow aus dem `Dockerfile`, damit CI und Image nicht auseinanderlaufen.

### Ausrollen

```bash
cd /opt/ionas.com
sed -i 's/^IONAS_VERSION=.*/IONAS_VERSION=2026-10-21/' .env
docker compose pull && docker compose up -d
```

Zurück auf eine ältere Fassung: alten Wert eintragen, dieselben zwei
Befehle.

Das Image ist zwei Schichten, damit ein Textdurchgang nicht den ganzen
Bildbestand neu überträgt. Am Registry gemessen:

| Schicht | komprimiert |
|---|---|
| Artikelbilder (`wissen/wp-content`) | 102,3 MB |
| übrige Seite (HTML, Assets, Pagefind-Index) | 24,0 MB |
| Caddy-Basis + Alpine | 24,9 MB |
| **erster Pull** | **151,2 MB** |

Ein Durchgang, der nur Texte anfasst, überträgt deshalb **24 MB**.

### Einmalig auf dem Server

```bash
mkdir -p /opt/ionas.com && cd /opt/ionas.com
# deploy/docker-compose.yml hierher kopieren
echo "IONAS_VERSION=2026-10-21" > .env
docker compose up -d
curl -sI http://127.0.0.1:8081/ | head -1        # erwartet: 200

# deploy/nginx-vhost.conf nach /etc/nginx/sites-available/ionas.com,
# Zertifikatspfade anpassen, verlinken, prüfen, neu laden:
nginx -t && systemctl reload nginx
```

Der Container läuft `read_only` mit `cap_drop: ALL`; zurückgegeben wird nur
`NET_BIND_SERVICE`, weil die Caddy-Binärdatei diese Capability als
Datei-Capability trägt und sonst schon das `exec` scheitert.

### Nach dem ersten Ausrollen prüfen

Die Kette nginx → Caddy ist lokal durchgetestet, inklusive Byte-Gleichheit
durch den Proxy. Diese vier Adressen trotzdem einmal von außen anfassen –
es sind die, an denen so etwas erfahrungsgemäß bricht:

```bash
for u in / /pc-hilfe/münchen /agb /wissen/feed/ /wissen/suche/; do
  curl -sI "https://www.ionas.com$u" | head -1
done
curl -sI https://www.ionas.com/pc-hilfe/muenchen | grep -i location   # 301
```

Und `/wissen/suche/` einmal im Browser öffnen und einen Begriff eintippen –
die Pagefind-Oberfläche ist das einzige Stück, das hier nicht im Browser
bedient wurde.

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

Eine Stelle ist bewusst **nicht** wortgleich übernommen: In Kommentar 701
hatte der Verfasser 2017 seine eigene Mailadresse genannt, weil sein Name
für Spam-Versand missbraucht wurde. Sie stand seither öffentlich auf
ionas.com und ist beim Umstieg durch `[E-Mail-Adresse entfernt]` ersetzt
worden – in `_build/wp/comments.json` und im zugehörigen
Referenz-Snapshot, damit sie auch beim Neuerzeugen nicht zurückkommt. Der
Satz bleibt lesbar. Die drei `adresse1@gmx.de`-Adressen in Kommentar 352
sind Platzhalter und unverändert.

### Drei Plugins ersetzt

| vorher | jetzt |
|---|---|
| simple-lightbox, 217 KB, neun Skriptdateien, jQuery | `webroot/static/js/lightbox.js`, 2 KB Vanilla-JS auf `<dialog>`. Greift dieselbe Auszeichnung ab (`<a href="bild.jpg"><img>`), kein Artikel musste angefasst werden |
| WordPress-Suche (`?s=`) | Pagefind unter `/wissen/suche/`, Index aus 150 Artikeln. Die Seitenleiste zeigt dorthin |
| Yoast SEO | `_partials/kopf-wissen.html` und `_partials/wissen-schema.html` |

### Die Schrift liegt lokal

Open Sans Condensed kam bis zum 21.10.2026 von `fonts.googleapis.com`. Damit
ging bei jedem Seitenaufruf die IP-Adresse des Besuchers an Google – nach
dem Urteil des LG München I (3 O 17493/20) ein DSGVO-Verstoß.

Die Dateien liegen jetzt in `webroot-eigen/static/fonts/`, eingebunden über
`webroot-eigen/static/css/fonts.css`. Übernommen sind nur die Bereiche
`latin` und `latin-ext` in zwei Schnitten (300, 700), jeweils als `woff2`
und `woff` – zusammen 122 KB, von denen ein Besucher typischerweise 15 KB
lädt. Die Lizenz (SIL OFL 1.1) liegt als `/static/fonts/OFL.txt` daneben,
wie die Lizenz es verlangt.

Neu dabei: `font-display: swap`. Der Text ist sofort in der Ersatzschrift
lesbar, statt bis zum Laden unsichtbar zu bleiben – Google lieferte das für
diese ältere API-Fassung nicht mit.

`_build/verify.py` normalisiert die eine geänderte `<link>`-Zeile, damit der
Byte-Vergleich den Rest der Seite weiter prüft.

### Toter Code im Kopf entfernt

Drei Zeilen standen wirkungslos in jeder Seite:

| | |
|---|---|
| `rel="author"`/`rel="publisher"` auf `plus.google.com` | Google+ ist seit April 2019 abgeschaltet |
| `alexaVerifyID` | Alexa ist seit Mai 2022 eingestellt |

Dazu eine Korrektur: `og:image` zeigte über **http** auf
`/images/ionas-logo-facebook.jpg` – eine Datei, die es nie gab und die auch
auf der alten Seite 404 lieferte. Jede Freigabe bei Facebook, LinkedIn oder
WhatsApp blieb deshalb ohne Vorschaubild. Jetzt über https auf
`/static/presse/ionas_logo_freigestellt.png`, das einzige eigene Bild, das
Facebooks Mindestmaß erfüllt (1000×479).

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

Zusätzlich fallen **406 Dateien mit 67 MB** weg, auf die keine einzige
ausgelieferte Seite verweist – weder per `src`/`href`/`srcset` noch über
`url()` in einem Stylesheet, `content` eines `<meta>` oder aus einer
Sitemap:

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

Der Scanner las anfangs nur `src`, `href`, `srcset` und `url()` – und
übersah damit `<meta property="og:image">`. 13 Bilder, die nur als
Vorschaubild für Facebook und Co. verlinkt sind, flogen dadurch raus; in der
ersten ausgerollten Fassung (`2026-10-21`) liefern sie 404, auf der alten
Seite taten sie es nicht. `linkcheck.py` und `verwaiste_assets.py` lesen
jetzt auch Bildangaben aus `<meta>`.

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

**Noch automatische Anfragen an Dritte.** Die Schrift ist lokal
(siehe unten), aber beim Laden einer Seite gehen weiterhin Anfragen raus:

| Ziel | Seiten | Auslöser |
|---|---|---|
| `www.youtube.com` | 80 | `<iframe>` mit `youtube.com/embed/…` – Städte- und Themenseiten zeigen alle dasselbe Video, dazu fünf Wissensartikel |
| `www.datamate.org` | 1 | zwei `<img>` auf der Startseite |
| `www.ionas-server.com` | 1 | ein `<img>` in einem Wissensartikel – liefert inzwischen 301 |

Das YouTube-Einbetten ist davon der wuchtigste Punkt: es kontaktiert Google
beim Seitenaufruf, nicht erst beim Klick. `youtube-nocookie.com` mildert das
nur (keine Cookies vor dem Abspielen, aber die Anfrage bleibt). Sauber wäre
ein Vorschaubild, das erst auf Klick das `<iframe>` nachlädt – das ist aber
ein Eingriff in 80 Seiten und keine Nebenbei-Änderung.

Die `rel="author"`/`rel="publisher"`-Verweise auf `plus.google.com` lösten
keine Anfrage aus (Browser holen solche `<link>`-Elemente nicht) und sind
inzwischen entfernt.

**`google-site-verification` und `msvalidate.01` stehen noch im Kopf.**
Bewusst: daran kann die Bestätigung der Property in der Search Console bzw.
bei Bing hängen, und ein Entfernen würde erst Monate später auffallen. Wer
prüft, dass beide Properties inzwischen per DNS oder Datei bestätigt sind,
kann die zwei Zeilen streichen.

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

## Was in `_build/` liegt und warum

`_build/` ist Migrationswerkzeug – aber **nicht** vollständig wegwerfbar,
denn zwei Teile daraus werden dauerhaft gebraucht:

| | |
|---|---|
| `verify.py`, `verify_wissen.py`, `linkcheck.py` | Die drei Prüfungen. Laufen bei **jedem Push** in GitHub Actions und sind das Sicherheitsnetz gegen stille Regressionen. |
| `reference/`, `reference-wissen/` (12 MB) | Die 270 gerenderten Seiten des alten Stands, gegen die geprüft wird. Ohne sie laufen `verify.py` und `verify_wissen.py` nicht. |
| `wp/` (9,6 MB) | Beiträge, Kommentare, Schlagwörter und Teaser als JSON. Sobald die WordPress-Datenbank abgeschaltet ist, ist das die **letzte maschinenlesbare Kopie** dieser Daten. |
| `gen_*.py`, `build.sh`, `tok.php`, `router-head.php` | Erzeugen `layouts/`, `content/`, `webroot/`, `data/` und `deploy/` aus dem alten Quellbaum. Nach dem Umstieg nur noch nötig, um die Umwandlung nachzuvollziehen. |
| `nicht-ausliefern.txt` | Die Liste der verwaisten Dateien. Wird von `gen_static.py` und `gen_wissen.py` gelesen. |

> **Achtung:** `build.sh` überschreibt `layouts/`, `content/`, `webroot/` und
> `data/` aus dem alten Quellbaum. Es ist ein Einmalwerkzeug. Wer die Seite
> pflegt, bearbeitet `content/` und `layouts/` direkt und ruft `build.sh`
> nicht mehr auf.

### Die Prüfungen laufen lassen

```bash
python3 _build/verify.py          # PHP-Teil, Seite für Seite
python3 _build/verify_wissen.py   # Wissensartikel
python3 _build/linkcheck.py       # alle seiteninternen Verweise
```

`linkcheck.py` kennt die Adressen, die erst der Webserver auflöst (`/agb`,
`/wissen/feed/`, die Weiterleitungen) und die zwölf Verweise, die schon vor
der Migration ins Leere liefen. Es meldet nur, was **neu** kaputt ist.

### Die Umwandlung wiederholen

Braucht den entpackten alten Quellbaum:

```bash
export IONAS_SRC=/pfad/zum/entpackten/website
_build/build.sh
hugo --gc
python3 _build/verify.py && python3 _build/verify_wissen.py
```

Ein Neulauf erzeugt bit-identisch denselben Stand – geprüft über
`git status` nach einem `rm -rf content webroot data`.

**`layouts/` gehört nicht dazu.** Dort liegen seit dem Auflösen von
`_build/templates/` auch handgeschriebene Dateien – die Templates des
Wissensbereichs –, die `build.sh` nicht erzeugt. `build.sh` prüft das beim
Start und bricht mit einem Hinweis ab, statt eine kaputte Seite zu bauen;
wiederherzustellen sind sie mit `git checkout -- layouts`.

Die Reihenfolge ist: `gen_layouts.py` (Gerüst aus dem Referenz-Render),
`gen_tpl.py` (Städte- und Themen-Template aus der PHP-Quelle),
`gen_content.py` (96 Seiten), `gen_static.py` (Assets + Sitemap),
`gen_wissen.py` (150 Artikel, Kommentare, Schlagwörter, Archive),
`gen_deploy.py` (Caddy, nginx, compose).

`gen_tpl.py` lässt PHP selbst tokenisieren (`tok.php`), statt mit Regexen
HTML von PHP zu trennen: in `pc-hilfe.php` überspannt ein `/* */`-Kommentar
mehrere `<?php ?>`-Blöcke, was per Regex nicht sicher zu erkennen ist. Jeder
PHP-Abschnitt ist dort einzeln auf sein Hugo-Pendant abgebildet; ein
unbekannter Abschnitt bricht den Lauf ab, statt stillschweigend Inhalt zu
verschlucken.

Den Referenz-Snapshot des PHP-Teils neu erzeugen:

```bash
cd /pfad/zum/entpackten/website && php -S 127.0.0.1:8899 index.php &
grep -oP "case\s+'\K[^']+" index.php | sort -u | while read r; do
  out="_build/reference/${r#/}"; [ "$r" = startseite ] && out="_build/reference"
  mkdir -p "$out"
  curl -sG --data-urlencode "p=$r" http://127.0.0.1:8899/ > "$out/index.html"
done
```

Eine Ausnahme: `/preise` zieht zwei Kundenstimmen per `SELECT` aus der
MySQL-Tabelle `bewertungen` und ist die einzige Seite, die ohne Datenbank in
einen Fatal Error läuft. Deren Referenz stammt deshalb von der Live-Seite;
die beiden Kundenstimmen stehen jetzt als HTML in `content/preise.html`.

## Zum alten Quellbaum

`functions.php` enthält MySQL- und SMTP-Zugangsdaten im Klartext und
`storage/contracts/` 60 Kundenvertrags-PDFs. Beides ist im neuen Webroot
nicht enthalten und wird mit Seite und Datenbank abgelöst – erledigt sich
also mit dem Umstieg.
