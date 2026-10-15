#!/bin/sh
# Renders the upstream proxies nginx.conf trusts to report the client address
# (X-Forwarded-For) and scheme (X-Forwarded-Proto), from TRUSTED_PROXY_CIDRS:
# comma-separated addresses or CIDRs. Default: the bundled Caddy terminator of
# docker-compose.prod.yml (172.28.0.10). Run by the nginx image entrypoint
# before nginx starts; a bad value stops the container instead of trusting
# the wrong peers.
set -eu
set -f  # entries are never globbed

cidrs="${TRUSTED_PROXY_CIDRS:-172.28.0.10}"
realip=/tmp/nginx-trusted-proxies.conf
geo=/tmp/nginx-trusted-proxies-geo.conf
: >"$realip"
: >"$geo"

n=0
for c in $(printf '%s' "$cidrs" | tr ',;' '  '); do
    case "$c" in
        *[!0-9A-Fa-f.:/]*)
            echo "$0: invalid TRUSTED_PROXY_CIDRS entry '$c'" >&2
            exit 1
            ;;
    esac
    printf 'set_real_ip_from %s;\n' "$c" >>"$realip"
    printf '%s 1;\n' "$c" >>"$geo"
    n=$((n + 1))
done

if [ "$n" -eq 0 ]; then
    echo "$0: TRUSTED_PROXY_CIDRS is empty" >&2
    exit 1
fi
echo "$0: trusting X-Forwarded-For/-Proto from: $(printf '%s' "$cidrs" | tr ';' ',')"
