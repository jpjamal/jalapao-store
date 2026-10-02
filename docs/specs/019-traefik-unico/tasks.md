# Tarefas

- [x] Middleware central `redirect-to-https` e Certbot central do IP no traefikproxy.
- [x] Cópia única do volume de certificados da loja para `infra_certificates`.
- [x] Teste de renovação (`--dry-run`) no deploy do traefikproxy.
- [x] Compose de deploy da loja só com labels; serviços com nome único.
- [x] Rota pública da API retirada; Admin mantido com router próprio.
- [x] `deploy.sh` com pré-requisitos, troca de nome e conferência pelo Traefik.
- [x] Cópia local com Traefik no lugar do Nginx.
- [x] Nginx e scripts dele removidos; documentação atualizada.
- [x] Ensaio local com Traefik central, certificado autoassinado e a loja de verdade.
- [x] Publicar (traefikproxy, depois a loja) e conferir em produção.
- [x] Renovação real pelo certbot central (01/10/2026, servida pelo Traefik sem intervenção).
- [ ] Apagar os volumes antigos `jalapao-store_certificates` e `jalapao-store_acme_webroot`
      (já liberados pela renovação; falta o dono autorizar o deploy que apaga).
- [x] Documentação da API: o Swagger apontava para `/jalapao-store/backend-api/schema/`, rota
      que deixou de existir; passou a usar o nome da rota, e a cópia local roteia `/api/v1/`.
