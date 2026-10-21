#!/usr/bin/env python3
"""Erzeugt die Auslieferungs-Konfiguration aus den tatsaechlichen Aliasen.

Die Aufgaben sind auf zwei Stellen verteilt:

  deploy/Caddyfile.container  Caddy im Image. Kennt nur :80 und macht alles,
                              was zur Seite gehoert: Weiterleitungen,
                              Rewrites, try_files, 404, Cache-Header. Diese
                              Regeln sind damit mit dem Inhalt versioniert.
  deploy/nginx-vhost.conf     Das native nginx davor. Macht nur, was dort
                              hingehoert: TLS, ionas.com -> www.ionas.com
                              und proxy_pass auf den Container.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import PRJ, write  # noqa: E402

PORT = 8081

# Verweise, die auf Dateien zeigen, welche unter einer anderen Adresse
# liegen. /agb stand bisher nur im nginx-vhost und nicht im Quellbaum.
REWRITES = [
    ('/agb', '/downloads/AGB-ionas.pdf', 'application/pdf',
     'Die AGB-PDF unter ihrer bisherigen Adresse. Die URL steht im Footer\n\t# jeder Seite und in der Sitemap. nginx lieferte sie bisher mit dem\n\t# falschen Typ text/html aus.'),
    ('/wissen/feed*', '/wissen/feed.xml', 'application/rss+xml; charset=utf-8',
     'Hugo legt den Feed als /wissen/feed.xml ab; ausgeliefert wird er unter\n\t# der bisherigen Adresse, die im Footer jeder Seite verlinkt ist.'),
]

# Weiterleitungen, die nicht aus den Alias-Feldern kommen.
EXTRA_REDIRS = [
    ('/Datenschutz', '/datenschutz',
     'So ist die URL in der Datenschutzerklaerung abgedruckt.'),
    ('/drucker-druckt-nicht/', '/wissen/drucker-druckt-nicht/', None),
    ('/datensicherung-mit-windows-bordmitteln/',
     '/wissen/datensicherung-mit-windows-bordmitteln/', None),
    ('/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/',
     '/wissen/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/',
     'Drei Wissensartikel verlinken aufeinander ohne das /wissen-Praefix.\n\t# Diese Adressen liefern auch im WordPress 404.'),
    ('/wissen/wlan-passwort-auslesen-so-einfach-gehts/'
     'wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/',
     '/wissen/wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/',
     'Ein Artikel verlinkt einen anderen relativ ohne fuehrenden Slash, der\n\t# Verweis landet dadurch unterhalb der eigenen Adresse.'),
]

# Pfade mit langer Cache-Zeit. Alles andere sind Seiten und bekommt eine
# kurze - dafuer braucht es einen Negativ-Matcher: die Seiten werden als
# /dienstleistung/ ausgeliefert, ein Muster auf *.html greift nie.
CACHE_LANG = ['/static/*', '/images/*', '/ionas-neu/*', '/senderlogos/*',
              '/downloads/*', '/themen/*', '/wissen/wp-content/*',
              '/pagefind/*']


def aliase():
    """Alias -> Zielpfad aus der Frontmatter aller Inhaltsdateien."""
    out = {}
    for cf in sorted(glob.glob(os.path.join(PRJ, 'content', '**', '*.html'),
                               recursive=True)):
        with open(cf, encoding='utf-8') as fh:
            kopf = fh.read().split('\n---\n', 1)[0]
        um = re.search(r'^url: "(.*?)"$', kopf, re.M)
        if not um:
            continue
        block = re.search(r'^aliases:\n((?:  - ".*"\n)+)', kopf + '\n', re.M)
        if not block:
            continue
        for a in re.findall(r'^  - "(.*?)"$', block.group(1), re.M):
            out[a] = um.group(1)
    return out


def caddyfile(al):
    zeilen = ['# Caddy im Container ionas-com. Kein TLS, kein Hostname: davor',
              '# steht das native nginx (siehe deploy/nginx-vhost.conf).',
              '#',
              '# Pruefen:',
              '#   docker run --rm -v ./deploy/Caddyfile.container:/c:ro \\',
              '#     caddy:2.11.7-alpine caddy validate --adapter caddyfile --config /c',
              '',
              ':80 {',
              '\troot * /srv',
              '\tencode zstd gzip',
              '']
    zeilen.append('\t# --- Weiterleitungen ------------------------------------------')
    zeilen.append('\t# ASCII-Schreibweisen der Umlaut-Landingpages und /rescue-stick.')
    zeilen.append('\t# Die canonical-Tags zeigten schon vorher auf die Umlaut-Variante,')
    zeilen.append('\t# der Inhalt wurde aber unter beiden Adressen mit 200 ausgeliefert.')
    for a, z in sorted(al.items()):
        zeilen.append('\tredir %s %s permanent' % (a, z))
    for a, z, kommentar in EXTRA_REDIRS:
        zeilen.append('')
        if kommentar:
            zeilen.append('\t# ' + kommentar)
        zeilen.append('\tredir %s %s permanent' % (a, z))
    zeilen.append('')

    for pfad, ziel, typ, kommentar in REWRITES:
        zeilen.append('\t# --- %s %s' % (pfad, '-' * max(0, 56 - len(pfad))))
        zeilen.append('\t# ' + kommentar)
        zeilen.append('\thandle %s {' % pfad)
        zeilen.append('\t\theader Content-Type "%s"' % typ)
        zeilen.append('\t\trewrite * %s' % ziel)
        zeilen.append('\t\tfile_server')
        zeilen.append('\t}')
        zeilen.append('')

    zeilen += [
        '\t# --- statische Auslieferung -----------------------------------',
        '\t# try_files bedient /dienstleistung und /dienstleistung/ gleich,',
        '\t# ohne Weiterleitung - genau wie das alte PHP.',
        '\thandle {',
        '\t\ttry_files {path} {path}/index.html',
        '\t\tfile_server',
        '\t}',
        '',
        '\thandle_errors {',
        '\t\trewrite * /404.html',
        '\t\tfile_server',
        '\t}',
        '',
        '\t# Lange Cache-Zeiten fuer Medien, kurze fuer die Seiten selbst.',
        '\t@medien path ' + ' '.join(CACHE_LANG),
        '\t@seiten not path ' + ' '.join(CACHE_LANG),
        '\theader @medien Cache-Control "public, max-age=2592000"',
        '\theader @seiten Cache-Control "public, max-age=300"',
        '',
        '\tlog {',
        '\t\toutput stdout',
        '\t\tformat console',
        '\t}',
        '}',
    ]
    write('deploy/Caddyfile.container', '\n'.join(zeilen) + '\n')


def nginx():
    write('deploy/nginx-vhost.conf', '''# vhost fuer das nativ installierte nginx auf dem Server.
#
# Hier steht nur, was zum Server gehoert: TLS, der kanonische Hostname und
# die Weitergabe an den Container. Alles, was zur Seite gehoert - die
# Weiterleitungen, /agb, der Feed, try_files, 404 - steckt im Image und ist
# dort mit dem Inhalt zusammen versioniert.
#
# Pfade zu den Zertifikaten an die bestehende Installation anpassen.

# Die Seite lief bisher ohne Host-Weiterleitung auf ionas.com UND
# www.ionas.com. Alle canonical-Tags zeigen auf www, deshalb hier eine
# echte 301 auf den kanonischen Host.
server {
    listen 80;
    listen [::]:80;
    server_name ionas.com www.ionas.com;
    return 301 https://www.ionas.com$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name ionas.com;

    ssl_certificate     /etc/letsencrypt/live/ionas.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ionas.com/privkey.pem;

    return 301 https://www.ionas.com$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name www.ionas.com;

    ssl_certificate     /etc/letsencrypt/live/ionas.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ionas.com/privkey.pem;

    access_log /var/log/nginx/ionas.com.access.log;
    error_log  /var/log/nginx/ionas.com.error.log;

    # Die Artikelbilder sind bis zu mehrere Megabyte gross.
    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:%d;
        proxy_http_version 1.1;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Caddy komprimiert selbst; nginx soll das nicht nochmal anfassen.
        proxy_set_header Accept-Encoding $http_accept_encoding;

        proxy_connect_timeout 5s;
        proxy_read_timeout    30s;
    }
}
''' % PORT)


def compose():
    write('deploy/docker-compose.yml', '''# Auf dem Server nach /opt/ionas.com/docker-compose.yml kopieren.
#
#   cd /opt/ionas.com
#   echo "IONAS_VERSION=2026-10-21" > .env
#   docker compose pull && docker compose up -d
#
# Ausrollen einer neuen Fassung: Version in .env aendern, dann dieselben
# zwei Befehle. Zurueck auf eine aeltere Fassung: alten Wert eintragen,
# dieselben zwei Befehle.

services:
    ionas-com:
        image: ${IONAS_IMAGE:-ghcr.io/datamate-rethink-it/ionas-com}:${IONAS_VERSION:?Bitte IONAS_VERSION in .env setzen, z.B. 2026-10-21}
        container_name: ionas-com
        restart: unless-stopped
        # Nur lokal erreichbar - davor steht das native nginx.
        ports:
            - 127.0.0.1:%d:80
        read_only: true
        tmpfs:
            - /tmp
            - /config
            - /data
        cap_drop:
            - ALL
        cap_add:
            # Die Caddy-Binaerdatei traegt cap_net_bind_service als
            # Datei-Capability. Ohne diese eine Rueckgabe scheitert schon das
            # exec ("operation not permitted").
            - NET_BIND_SERVICE
        security_opt:
            - no-new-privileges:true
        healthcheck:
            test: ['CMD', 'wget', '--spider', '-q', 'http://127.0.0.1/']
            interval: 30s
            timeout: 5s
            retries: 3
            start_period: 5s
        logging:
            driver: json-file
            options:
                max-size: 10m
                max-file: '3'
''' % PORT)


def main():
    al = aliase()
    for alt in ('deploy/Caddyfile', 'deploy/nginx-ionas.conf'):
        pfad = os.path.join(PRJ, alt)
        if os.path.isfile(pfad):
            os.remove(pfad)
    caddyfile(al)
    nginx()
    compose()
    print('deploy/ erzeugt:')
    print('  Caddyfile.container   %d Weiterleitungen aus Aliasen + %d weitere, '
          '%d Rewrites' % (len(al), len(EXTRA_REDIRS), len(REWRITES)))
    print('  nginx-vhost.conf      TLS, ionas.com -> www, proxy_pass :%d' % PORT)
    print('  docker-compose.yml    fuer /opt/ionas.com/ auf dem Server')


if __name__ == '__main__':
    main()
