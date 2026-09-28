#!/usr/bin/env bash
# Publicação na VPS, chamada pelo GitHub Actions depois do rsync. Proxy, HTTPS e certificados
# são do traefikproxy (spec 019); aqui só a aplicação: backup, migrações, subida e conferência.
set -euo pipefail
cd "$(dirname "$0")/.."
test -s .env.backend
# Chave da loja no servidor de arquivos (SILO): gerada na VPS pelo traefikproxy, lida de lá.
silo_env="$HOME/traefikproxy/.env.silo.jalapao-store"
dc() {
    local env_files=(--env-file .env.production --env-file .env.backend --env-file "$silo_env")
    if [ -s .env.marketplace ]; then
        env_files+=(--env-file .env.marketplace)
    fi
    docker compose -f docker-compose.deploy.yml "${env_files[@]}" "$@"
}

# A loja depende da infraestrutura central: as redes do Traefik e do SILO, o volume do
# certificado do IP e a chave do SILO. Sem elas o compose falharia no meio do deploy, com a
# API já parada. Melhor recusar antes.
for requisito in "network:traefik_proxy" "network:infra_storage" "volume:infra_certificates"; do
    tipo=${requisito%%:*}; nome=${requisito#*:}
    if ! docker "$tipo" inspect "$nome" >/dev/null 2>&1; then
        echo "Falta o $tipo '$nome' do traefikproxy. Publique o traefikproxy antes." >&2
        exit 1
    fi
done
if [ ! -s "$silo_env" ]; then
    echo "Falta $silo_env (chave da loja no SILO). Publique o traefikproxy antes." >&2
    exit 1
fi

mkdir -p "$HOME/backups/jalapao-store"
chmod 700 "$HOME/backups/jalapao-store"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
dc build

# Congela as escritas comerciais antes do backup e das migrações. Na troca de nome dos
# serviços (spec 019) os containers antigos ainda se chamam db/backend: para eles também.
dc stop jalapao-backend 2>/dev/null || true
docker stop jalapao-store-backend-1 2>/dev/null || true
banco=$(docker ps --format '{{.Names}}' | grep -E '^jalapao-store-(jalapao-)?db-1$' | head -1 || true)
if [ -n "$banco" ]; then
    docker exec "$banco" pg_dump -U jalapao -d jalapao -Fc > "$HOME/backups/jalapao-store/db-$stamp.dump"
    test -s "$HOME/backups/jalapao-store/db-$stamp.dump"
    chmod 600 "$HOME/backups/jalapao-store/db-$stamp.dump"
fi

# Troca de nome: o banco antigo solta o volume antes de o novo subir com ele.
docker stop jalapao-store-db-1 2>/dev/null || true
dc up -d --wait jalapao-db
dc run --rm jalapao-backend python manage.py migrate --noinput

# Fotos (spec 020): moram no bucket jalapao-media do SILO. As de antes estão no volume antigo,
# montado só para leitura; a cópia é idempotente (o que já está no bucket fica) e nunca apaga o
# disco. Ainda com a escrita congelada, o backup das fotos sai do bucket, junto com o do banco.
dc run --rm -T jalapao-backend python manage.py migrate_media_to_storage /app/media-disco
dc run --rm -T jalapao-backend python manage.py export_media > "$HOME/backups/jalapao-store/media-$stamp.tar.gz"
tar -tzf "$HOME/backups/jalapao-store/media-$stamp.tar.gz" >/dev/null
chmod 600 "$HOME/backups/jalapao-store/media-$stamp.tar.gz"

# Manuais em PDF: a pasta manuais/ da VPS alimenta o bucket público jalapao-manuais. Só entra o
# que ainda não está lá — um PDF trocado pelo painel do SILO não é sobrescrito pelo do disco.
if [ -d manuais ] && [ -n "$(ls -A manuais)" ]; then
    docker run --rm --network infra_storage -v "$PWD/manuais:/manuais:ro" --env-file "$silo_env" \
        --entrypoint sh pgsty/mc:RELEASE.2026-09-16T00-00-00Z -c \
        'export MC_HOST_silo="http://$S3_ACCESS_KEY:$S3_SECRET_KEY@silo:9000"; mc mirror --quiet /manuais silo/jalapao-manuais'
fi
legacy_running=$(docker ps -q --filter name='^jalapao-api$')
if [ -n "$legacy_running" ]; then docker stop jalapao-api; fi
trap 'if [ -n "$legacy_running" ]; then docker start jalapao-api; fi' ERR
if [ -s dados/produtos.json ]; then
    cp dados/produtos.json "$HOME/backups/jalapao-store/products-$stamp.json"
    chmod 600 "$HOME/backups/jalapao-store/products-$stamp.json"
    dc run --rm jalapao-backend python manage.py import_legacy /legacy/produtos.json
fi
if [ -s .env.bootstrap ]; then
    dc run --rm --env-from-file .env.bootstrap jalapao-backend python manage.py bootstrap_users
fi
# --remove-orphans tira os serviços que saíram: gateway, tls, certbot e os de nome antigo.
dc up -d --wait --remove-orphans
legacy_running=''
trap - ERR

# Conferência pelo caminho real (Traefik). O Traefik descobre as rotas pelos labels em
# segundos e, até lá, responde 404: por isso cada checagem espera o código certo (até 60 s).
espera() {
    local esperado=$1 url=$2 codigo=000
    for _ in $(seq 1 20); do
        codigo=$(curl --silent --output /dev/null --write-out '%{http_code}' "$url" || true)
        case " $esperado " in *" $codigo "*) return 0 ;; esac
        sleep 3
    done
    echo "Esperava $esperado em $url e recebi $codigo." >&2
    return 1
}
# um manual qualquer da pasta, para provar a rota /manuais/ → bucket (espaço vira %20)
manual=$(ls manuais 2>/dev/null | head -1 | sed 's/ /%20/g' || true)
for host in 217.216.82.25 jpsys.duckdns.org; do
    espera 200 "https://$host/jalapao-store/login"
    espera 200 "https://$host/jalapao-store/admin/login/"
    # a API não tem mais rota pública: o caminho cai no front, que responde 404
    espera 404 "https://$host/jalapao-store/backend-api/products"
    espera "301 308" "http://$host/jalapao-store/login"
    if [ -n "${manual:-}" ]; then espera 200 "https://$host/manuais/$manual"; fi
done
echo "   rotas conferidas: front 200, admin 200, API sem rota pública, HTTP → HTTPS, manuais"
dc ps
