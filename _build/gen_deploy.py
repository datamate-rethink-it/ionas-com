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
# Deploy:  hugo --gc --minify  &&  rsync -a --delete public/ server:/var/www/ionas/
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

\t# --- WordPress bleibt, wo es ist ---------------------------------
\t# Alles unter /wissen geht unveraendert an das bestehende WordPress.
\t# Adresse an die eigene Installation anpassen.
\thandle /wissen* {
\t\treverse_proxy 127.0.0.1:8080
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
\t@assets path /static/* /images/* /ionas-neu/* /senderlogos/*
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

# /wissen bleibt WordPress (bestehende location-Bloecke unveraendert lassen!)

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

location ~* ^/(static|images|ionas-neu|senderlogos)/ {
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
