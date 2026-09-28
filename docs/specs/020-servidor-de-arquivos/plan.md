# Plano

## traefikproxy
- Serviço `silo` (`pgsty/silo:RELEASE.2026-09-16T00-00-00Z`), volume `infra_silo_data`,
  redes `traefik_proxy` (painel e buckets públicos) e `infra_storage` (API S3 para os
  backends; os fronts não entram nela).
- `silo/publicar.sh`, chamado pelo deploy: gera `.env.silo` (raiz) e `.env.silo.<sistema>` na
  primeira vez (fora do rsync, modo 600), sobe o SILO e roda `silo/provisionar.sh` dentro dele.
- `silo/provisionar.sh` (idempotente): buckets, política por sistema (leitura e escrita só nos
  buckets dele), usuário por sistema e a leitura pública de objeto do bucket de manuais.
- Painel em `https://jpsys.duckdns.org/silo` (só pelo domínio; limite de requisições), login
  com a credencial raiz de `~/traefikproxy/.env.silo`.

## jalapao-store
- `django-storages[s3]` 1.14.6. `STORAGES["default"]` vira `S3Storage` quando existe
  `S3_ENDPOINT_URL`: estilo de endereço por caminho, sem ACL por objeto, sem sobrescrever.
- Comandos: `migrate_media_to_storage <pasta>` (disco → armazenamento, mesma chave,
  idempotente) e `export_media` (tar.gz na saída padrão; retirado em 28/09 junto com o backup
  de arquivos).
- Compose: variáveis `S3_*` (a chave vem por `--env-file` de `~/traefikproxy/.env.silo.jalapao-store`),
  rede `infra_storage`, `product_media` montado só para leitura em `/app/media-disco`, routers
  `/manuais/` → `silo-s3@docker` com `replacepathregex` para `/jalapao-manuais/<arquivo>`.
- `deploy.sh`: confere a rede e a chave do SILO; depois das migrations, migra as fotos,
  exporta o backup delas do bucket, espelha a pasta `manuais/` (`mc mirror` sem
  sobrescrever) e confere um manual pelos dois hosts.
- CI: variáveis fictícias `S3_*` para validar o compose.
