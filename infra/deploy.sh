#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -s .env.backend
dc() {
    local env_files=(--env-file .env.production --env-file .env.backend)
    if [ -s .env.marketplace ]; then
        env_files+=(--env-file .env.marketplace)
    fi
    docker compose -f docker-compose.deploy.yml "${env_files[@]}" "$@"
}
if [ -n "$(dc ps -q tls)" ]; then export COMPOSE_PROFILES=https; fi
mkdir -p "$HOME/backups/jalapao-store"
chmod 700 "$HOME/backups/jalapao-store"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
dc build
# Freeze commercial writes before the backup and valuation migrations.
# On failure leave the API stopped for inspection; never serve old valuation logic.
dc stop backend
if dc ps --status running --services | grep -qx db; then
    dc exec -T db pg_dump -U jalapao -d jalapao -Fc > "$HOME/backups/jalapao-store/db-$stamp.dump"
    test -s "$HOME/backups/jalapao-store/db-$stamp.dump"
    chmod 600 "$HOME/backups/jalapao-store/db-$stamp.dump"
fi
dc up -d --wait db
dc run --rm backend python manage.py migrate --noinput
legacy_running=$(docker ps -q --filter name='^jalapao-api$')
if [ -n "$legacy_running" ]; then docker stop jalapao-api; fi
trap 'if [ -n "$legacy_running" ]; then docker start jalapao-api; fi' ERR
if [ -s dados/produtos.json ]; then
    cp dados/produtos.json "$HOME/backups/jalapao-store/products-$stamp.json"
    chmod 600 "$HOME/backups/jalapao-store/products-$stamp.json"
    dc run --rm backend python manage.py import_legacy /legacy/produtos.json
fi
if [ -s .env.bootstrap ]; then
    dc run --rm --env-from-file .env.bootstrap backend python manage.py bootstrap_users
fi
dc up -d --wait --remove-orphans db backend frontend gateway
legacy_running=''
trap - ERR
if ! dc run --rm --no-deps --entrypoint sh certbot -c 'test -s /etc/letsencrypt/live/jalapao-ip/fullchain.pem'; then
    dc run --rm --no-deps --entrypoint certbot certbot certonly \
      --webroot -w /var/www/certbot --ip-address 217.216.82.25 \
      --preferred-profile shortlived --cert-name jalapao-ip --non-interactive \
      --agree-tos --register-unsafely-without-email
fi
if ! dc run --rm --no-deps --entrypoint sh certbot -c 'test -s /etc/letsencrypt/live/jalapao-domain/fullchain.pem'; then
    dc run --rm --no-deps --entrypoint certbot certbot certonly \
      --webroot -w /var/www/certbot -d jalapao-store.217-216-82-25.sslip.io \
      --cert-name jalapao-domain --non-interactive \
      --agree-tos --register-unsafely-without-email
fi
if ! dc run --rm --no-deps --entrypoint sh certbot -c 'test -s /etc/letsencrypt/live/jalapao-duckdns/fullchain.pem'; then
    dc run --rm --no-deps --entrypoint certbot certbot certonly \
      --webroot -w /var/www/certbot -d jalapao-store.duckdns.org \
      --cert-name jalapao-duckdns --non-interactive \
      --agree-tos --register-unsafely-without-email
fi
dc --profile https up -d --wait --remove-orphans
# Bind-mounted config files can keep an old inode after rsync replaces the host file.
# Recreate only this project's proxies, also refreshing upstream DNS after app replacement.
dc --profile https up -d --wait --force-recreate --no-deps gateway tls
curl --fail --silent --show-error --retry 6 --retry-delay 3 https://217.216.82.25/health
curl --fail --silent --show-error --retry 6 --retry-delay 3 https://jalapao-store.217-216-82-25.sslip.io/health
curl --fail --silent --show-error --retry 6 --retry-delay 3 https://jalapao-store.duckdns.org/health
dc run --rm --no-deps --entrypoint sh certbot -c 'touch /var/www/certbot/.https-ready'
curl --fail --silent --show-error --output /dev/null https://217.216.82.25/jalapao-store/login
curl --fail --silent --show-error --output /dev/null https://jalapao-store.217-216-82-25.sslip.io/jalapao-store/login
curl --fail --silent --show-error --output /dev/null https://jalapao-store.duckdns.org/jalapao-store/login
test "$(curl --silent --output /dev/null --write-out '%{http_code}' http://217.216.82.25/jalapao-store/login)" = 308
dc --profile https ps
