# Tarefas

- [x] Pesquisa de servidores de arquivos e escolha do dono (SILO, AGPLv3).
- [x] SILO no traefikproxy: serviço, rede `infra_storage`, credenciais geradas na VPS,
      provisionamento idempotente, painel em `/silo`.
- [x] `S3Storage` nas fotos quando configurado; disco sem configuração.
- [x] Comandos `migrate_media_to_storage` e `export_media`, com testes.
- [x] Rota `/manuais/` para o bucket público, sem listagem.
- [x] `deploy.sh`: migração, backup do bucket, espelho dos manuais, conferência.
- [x] Ensaio com SILO de verdade atrás do Traefik local.
- [x] Publicar e conferir em produção (fotos migradas, manual pelo QR code).
- [ ] Depois de conferido: tirar o volume `product_media` do compose e apagar a pasta
      `manuais/` da VPS (a fonte passa a ser só o bucket).
- [ ] Backup para fora da VPS (os buckets e os dumps ainda moram na mesma máquina).
