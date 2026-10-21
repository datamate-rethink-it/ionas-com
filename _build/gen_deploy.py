#!/usr/bin/env python3
"""Erzeugt Caddyfile und nginx-Snippet aus den tatsaechlichen Aliasen."""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import *


def aliases():
    """Alias -> Zielpfad aus der Frontmatter aller Inhaltsdateien."""
    out = {}
    for cf in sorted(glob.glob(os.path.join(PRJ, 'content', '**', '*.html'),
                               recursive=True)):
        with open(cf, encoding='utf-8') as fh:
            head = fh.read().split('\n---\n', 1)[0]
        um = re.search(r'^url: "(.*?)"$', head, re.M)
        if not um:
            continue
        target = um.group(1)
        block = re.search(r'^aliases:\n((?:  - ".*"\n)+)', head + '\n', re.M)
        if not block:
            continue
        for a in re.findall(r'^  - "(.*?)"$', block.group(1), re.M):
            out[a] = target
    return out


def main():
    al = aliases()
    redirs = '\n'.join('\tredir %s %s permanent' % (a, t)
                       for a, t in sorted(al.items()))

    write('deploy/Caddyfile', '''# ionas.com - statisch aus Hugo, /wissen weiterhin WordPress.
#
# Deploy:  hugo --gc
#          npx pagefind --site public        (Suchindex fuer /wissen/suche/)
#          rsync -a --delete public/ server:/var/www/ionas/
# Pruefen: caddy validate --config /etc/caddy/Caddyfile

# Die Seite lief bisher ohne Host-Weiterleitung auf ionas.com UND
# www.ionas.com. Alle canonical-Tags zeigen auf www, deshalb hier eine
# echte 301 auf den kanonischen Host.
ionas.com {
\tredir https://www.ionas.com{uri} permanent
}

www.ionas.com {
\troot * /var/www/ionas
\tencode zstd gzip

\t# --- /wissen/feed/ ----------------------------------------------
\t# Hugo legt den Feed als /wissen/feed.xml ab; ausgeliefert wird er
\t# unter der bisherigen Adresse, die im Footer jeder Seite steht.
\thandle /wissen/feed* {
\t\theader Content-Type "application/rss+xml; charset=utf-8"
\t\trewrite * /wissen/feed.xml
\t\tfile_server
\t}

\t# --- /agb liefert die AGB als PDF -------------------------------
\t# Das war bisher eine Rewrite-Regel im nginx-vhost (und lieferte das
\t# PDF faelschlich als text/html aus). Die URL steht in der Sitemap und
\t# im Footer jeder Seite, muss also erhalten bleiben.
\thandle /agb {
\t\theader Content-Type application/pdf
\t\trewrite * /downloads/AGB-ionas.pdf
\t\tfile_server
\t}

\t# --- Weiterleitungen --------------------------------------------
\t# In der Datenschutzerklaerung ist die URL mit grossem D abgedruckt.
\tredir /Datenschutz /datenschutz permanent

\t# Drei Wissensartikel verlinken aufeinander ohne das /wissen-Praefix.
\t# Diese Adressen liefern auch im WordPress 404; die Weiterleitung
\t# repariert sie, ohne die Artikeltexte anzufassen.
\tredir /drucker-druckt-nicht/ /wissen/drucker-druckt-nicht/ permanent
\tredir /datensicherung-mit-windows-bordmitteln/ /wissen/datensicherung-mit-windows-bordmitteln/ permanent
\tredir /malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/ /wissen/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/ permanent

\t# Ein Artikel verlinkt einen anderen relativ ohne fuehrenden Slash, der
\t# Verweis landet dadurch unterhalb der eigenen Adresse. Auch im
\t# WordPress eine 404.
\tredir /wissen/wlan-passwort-auslesen-so-einfach-gehts/wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/ /wissen/wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/ permanent

\t# ASCII-Schreibweisen der Umlaut-Landingpages. Hugo legt dafuer
\t# zusaetzlich meta-refresh-Seiten ab; diese 301 ist das Saubere und
\t# greift zuerst.
%s

\t# --- statische Auslieferung -------------------------------------
\t# try_files bedient /dienstleistung und /dienstleistung/ gleich,
\t# ohne Weiterleitung - genau wie bisher.
\thandle {
\t\ttry_files {path} {path}/index.html
\t\tfile_server
\t}

\thandle_errors {
\t\trewrite * /404.html
\t\tfile_server
\t}

\t# Lange Cache-Zeiten fuer Assets, keine fuer HTML.
\t@assets path /static/* /images/* /ionas-neu/* /senderlogos/* /wissen/wp-content/* /pagefind/*
\theader @assets Cache-Control "public, max-age=2592000"
\theader /*.html Cache-Control "public, max-age=300"
}
''' % redirs)

    nginx = '\n'.join('    rewrite ^%s$ %s permanent;' % (re.escape(a), t)
                      for a, t in sorted(al.items()))
    write('deploy/nginx-ionas.conf', '''# Variante fuer den bestehenden nginx, falls kein Caddy zum Einsatz kommt.
# In den server-Block fuer www.ionas.com einsetzen.

root /var/www/ionas;
charset utf-8;

# /wissen/feed/ liefert die von Hugo erzeugte /wissen/feed.xml
location ~ ^/wissen/feed/?$ {
    default_type "application/rss+xml; charset=utf-8";
    alias /var/www/ionas/wissen/feed.xml;
}

# Drei Wissensartikel verlinken aufeinander ohne /wissen-Praefix
location = /drucker-druckt-nicht/ { return 301 /wissen/drucker-druckt-nicht/; }
location = /datensicherung-mit-windows-bordmitteln/ { return 301 /wissen/datensicherung-mit-windows-bordmitteln/; }
location = /malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/ { return 301 /wissen/malware-die-allgegenwaertige-vermeidbare-gefahr-fuer-ihren-computer/; }
location = /wissen/wlan-passwort-auslesen-so-einfach-gehts/wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/ { return 301 /wissen/wlan-funktioniert-nicht-schritt-fuer-schritt-zum-ziel/; }

# /agb lieferte bisher downloads/AGB-ionas.pdf - hier mit korrektem Typ.
location = /agb {
    default_type application/pdf;
    alias /var/www/ionas/downloads/AGB-ionas.pdf;
}

location = /Datenschutz { return 301 /datenschutz; }

# ASCII-Schreibweisen der Umlaut-Landingpages
%s

# Extensionslose URLs auf die Verzeichnis-Indizes
location / {
    try_files $uri $uri/index.html $uri/ =404;
}

error_page 404 /404.html;
location = /404.html { internal; }

location ~* ^/(static|images|ionas-neu|senderlogos|pagefind|wissen/wp-content)/ {
    expires 30d;
    add_header Cache-Control "public";
}
''' % nginx)

    print('deploy/Caddyfile und deploy/nginx-ionas.conf erzeugt (%d Weiterleitungen)'
          % len(al))
    for a, t in sorted(al.items()):
        print('   %-28s -> %s' % (a, t))


if __name__ == '__main__':
    main()
