# syntax=docker/dockerfile:1
#
# ionas.com als ausliefernder Container: Caddy mit der fertig gebauten
# Seite. Kein TLS, kein Hostname - davor steht das native nginx des
# Servers (siehe deploy/nginx-vhost.conf).
#
# Der Build ist in sich geschlossen: ein frischer Clone genuegt, es braucht
# weder den alten PHP-Quellbaum noch Node. Die Werkzeuge in _build/ sind
# Migrationswerkzeug und nicht Teil des Builds.
#
#   docker build -t ionas-com:dev .
#   docker run --rm -p 127.0.0.1:8081:80 ionas-com:dev

ARG HUGO_VERSION=0.168.0
ARG PAGEFIND_VERSION=1.4.0
ARG CADDY_VERSION=2.11.7

# ---------------------------------------------------------------- Build
FROM debian:trixie-slim AS builder

ARG HUGO_VERSION
ARG PAGEFIND_VERSION

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Hugo Extended als vorgebaute Binaerdatei - die Seite braucht keinen
# SCSS-Compiler, aber es ist dieselbe Fassung, gegen die geprueft wurde.
# Pagefind als eigenstaendige musl-Binaerdatei, damit kein Node ins Bild
# muss (die npm-Fassung laedt genau diese Datei nach).
RUN set -eux; \
    curl -fsSL -o /tmp/hugo.tar.gz \
      "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz"; \
    tar -C /usr/local/bin -xzf /tmp/hugo.tar.gz hugo; \
    curl -fsSL -o /tmp/pagefind.tar.gz \
      "https://github.com/CloudCannon/pagefind/releases/download/v${PAGEFIND_VERSION}/pagefind-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz"; \
    tar -C /usr/local/bin -xzf /tmp/pagefind.tar.gz; \
    rm /tmp/hugo.tar.gz /tmp/pagefind.tar.gz; \
    hugo version; \
    pagefind --version

WORKDIR /src
COPY . /src

# Kein --minify: das gaebe die Byte-Gleichheit mit dem bisherigen Stand auf,
# die _build/verify.py nachweist.
RUN set -eux; \
    hugo --gc --destination /src/public; \
    pagefind --site /src/public; \
    test -f /src/public/wissen/drucker-druckt-nicht/index.html; \
    test -f /src/public/pagefind/pagefind-ui.js; \
    cp -al /src/public /src/site; \
    rm -rf /src/site/wissen/wp-content

# ---------------------------------------------------------------- Laufzeit
FROM caddy:${CADDY_VERSION}-alpine

COPY deploy/Caddyfile.container /etc/caddy/Caddyfile

# Zwei Schichten mit Absicht: die 102 MB Artikelbilder aendern sich fast
# nie, der Rest bei jedem Textdurchgang. Ein Inhalts-Release uebertraegt
# dadurch ~46 MB statt 148.
COPY --from=builder /src/public/wissen/wp-content /srv/wissen/wp-content
COPY --from=builder /src/site /srv

LABEL org.opencontainers.image.title="ionas.com" \
      org.opencontainers.image.description="ionas.com als statische Seite (Hugo) mit Caddy" \
      org.opencontainers.image.source="https://github.com/datamate-rethink-it/ionas-com" \
      org.opencontainers.image.licenses="UNLICENSED"

EXPOSE 80
