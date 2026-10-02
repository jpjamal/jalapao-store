# Tarefas

- [x] Pesquisa de servidores de arquivos e escolha do dono (SILO, AGPLv3).
- [x] SILO no traefikproxy: serviço, rede `infra_storage`, credenciais geradas na VPS,
      provisionamento idempotente, painel em `/silo`.
- [x] `S3Storage` nas fotos quando configurado; disco sem configuração.
- [x] Comandos `migrate_media_to_storage` e `export_media`, com testes.
- [x] Rota `/manuais/` para o bucket público, sem listagem.
- [x] `deploy.sh`: migração, backup do bucket, espelho dos manuais, conferência (migração,
      backup e espelho saíram em 28/09, depois de cumprirem o papel).
- [x] Ensaio com SILO de verdade atrás do Traefik local.
- [x] Publicar e conferir em produção (fotos migradas, manual pelo QR code).
- [x] Tirar o volume `product_media` do compose e apagar o volume e a pasta `manuais/` da VPS
      (a fonte passa a ser só o bucket) — pedido do dono em 28/09.
- [x] ~~Backup dos buckets~~ — descartado pelo dono em 28/09: o deploy não copia arquivos, e o
      comando `export_media` saiu.
