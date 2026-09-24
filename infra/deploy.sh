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
# Quem termina TLS é decisão, não adivinhação: JALAPAO_TLS, variável do repositório no
# GitHub, que chega aqui pelo .env.production.
#   nginx   (padrão) → o Nginx da loja segura a 443
#   traefik          → o Nginx da loja solta a 443 para o Traefik assumir
# A virada acontece só por deploy, nunca por comando na VPS.
JALAPAO_TLS=$(grep -m1 '^JALAPAO_TLS=' .env.production 2>/dev/null | cut -d= -f2- | tr -d "\"' \r" || true)
JALAPAO_TLS=${JALAPAO_TLS:-nginx}
case "$JALAPAO_TLS" in nginx|traefik) ;; *)
    echo "JALAPAO_TLS inválido: '$JALAPAO_TLS'. Use nginx ou traefik." >&2
    exit 1
esac

# A porta que o Traefik publica é lida do container. Procurar "443->443" no texto das
# portas casaria também com a pré-validação "127.0.0.1:8443->443/tcp"; por isso exige
# HostPort 443 fora do loopback.
traefik_publica_443() {
    docker inspect traefikproxy-traefik-1 \
        --format '{{range index .NetworkSettings.Ports "443/tcp"}}{{.HostIp}} {{.HostPort}}{{"\n"}}{{end}}' \
        2>/dev/null \
      | awk '$2 == "443" && $1 != "127.0.0.1" && $1 != "::1" { achou = 1 } END { exit !achou }'
}

if [ "$JALAPAO_TLS" = nginx ]; then
    # Configuração inconsistente: pedir o Nginx na 443 com o Traefik já nela faria o
    # container falhar ao subir no meio do deploy. Melhor recusar com o motivo.
    if traefik_publica_443; then
        echo "JALAPAO_TLS=nginx, mas o Traefik já publica a 443." >&2
        echo "Troque para JALAPAO_TLS=traefik, ou volte o Traefik para a pré-validação." >&2
        exit 1
    fi
    echo "   HTTPS: Nginx da loja na 443 (JALAPAO_TLS=nginx)."
    export COMPOSE_PROFILES=nginx-https
else
    echo "   HTTPS: Traefik assume a 443 (JALAPAO_TLS=traefik); o Nginx TLS sai."
fi
# O Certbot avisa o Traefik tocando o dynamic.yml do projeto vizinho. Se a pasta não
# estiver onde se espera, o certificado do IP renovaria sem o Traefik reler — falha
# silenciosa, do tipo que só aparece quando o site cai. Melhor recusar agora.
if [ ! -d ../traefikproxy/traefik ]; then
    echo "Esperava ~/traefikproxy/traefik ao lado deste projeto e não encontrei." >&2
    echo "O Certbot precisa dela para avisar o Traefik depois de renovar o certificado do IP." >&2
    exit 1
fi
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
# As fotos não ficam no PostgreSQL. Guardar o volume na mesma janela de escrita congelada.
dc run --rm --no-deps -T --entrypoint python backend -c \
    'import sys, tarfile; archive = tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz"); archive.add("/app/media", arcname="media"); archive.close()' \
    > "$HOME/backups/jalapao-store/media-$stamp.tar.gz"
test -s "$HOME/backups/jalapao-store/media-$stamp.tar.gz"
tar -tzf "$HOME/backups/jalapao-store/media-$stamp.tar.gz" >/dev/null
chmod 600 "$HOME/backups/jalapao-store/media-$stamp.tar.gz"
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
test "$(dc exec -T gateway wget -qO- http://127.0.0.1:8080/health)" = ok
legacy_running=''
trap - ERR
if ! dc run --rm --no-deps --entrypoint sh certbot -c 'test -s /etc/letsencrypt/live/jalapao-ip/fullchain.pem'; then
    dc run --rm --no-deps --entrypoint certbot certbot certonly \
      --webroot -w /var/www/certbot --ip-address 217.216.82.25 \
      --preferred-profile shortlived --cert-name jalapao-ip --non-interactive \
      --agree-tos --register-unsafely-without-email
fi
if [ "${COMPOSE_PROFILES:-}" = nginx-https ] && ! dc run --rm --no-deps --entrypoint sh certbot -c 'test -s /etc/letsencrypt/live/jpsys-duckdns/fullchain.pem'; then
    dc run --rm --no-deps --entrypoint certbot certbot certonly \
      --webroot -w /var/www/certbot -d jpsys.duckdns.org \
      --cert-name jpsys-duckdns --non-interactive \
      --agree-tos --register-unsafely-without-email
fi
dc up -d --wait --remove-orphans
# Bind-mounted config files can keep an old inode after rsync replaces the host file.
# Recreate only this project's proxies, also refreshing upstream DNS after app replacement.
dc up -d --wait --force-recreate --no-deps gateway
if [ "$JALAPAO_TLS" = nginx ]; then
    dc up -d --wait --force-recreate --no-deps tls
else
    # `up --remove-orphans` não garante parar um serviço cujo perfil foi desligado:
    # ele continua definido no arquivo. Tirar da 443 precisa ser explícito.
    dc --profile nginx-https rm -sf tls || true
fi

# Na virada, a loja solta a 443 antes de o Traefik assumir — os dois não podem segurar a
# porta ao mesmo tempo. Nesse intervalo não há HTTPS, e verificar agora só daria um erro
# enganoso. O deploy do traefikproxy é quem completa a virada e valida.
if [ "$JALAPAO_TLS" = traefik ] && ! traefik_publica_443; then
    echo "" >&2
    echo "ATENÇÃO: o Nginx soltou a 443 e o Traefik ainda não assumiu. HTTPS fora do ar." >&2
    echo "Publique agora o traefikproxy com TRAEFIK_HTTPS_BIND=0.0.0.0:443 para completar." >&2
    dc ps
    exit 0
fi

curl --fail --silent --show-error --retry 6 --retry-delay 3 https://217.216.82.25/health
# Domínio novo: o Traefik só emite o certificado quando a rota aparece, e até lá entrega
# o certificado do IP. --retry sozinho não repete erro de certificado; --retry-all-errors sim.
curl --fail --silent --show-error --retry 20 --retry-delay 3 --retry-all-errors https://jpsys.duckdns.org/health
dc run --rm --no-deps --entrypoint sh certbot -c 'touch /var/www/certbot/.https-ready'
curl --fail --silent --show-error --output /dev/null https://217.216.82.25/jalapao-store/login
curl --fail --silent --show-error --output /dev/null https://jpsys.duckdns.org/jalapao-store/login
test "$(curl --silent --output /dev/null --write-out '%{http_code}' http://217.216.82.25/jalapao-store/login)" = 308
dc ps
