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
- [ ] Publicar (traefikproxy, depois a loja) e conferir em produção.
- [ ] Apagar o volume antigo `jalapao-store_certificates` depois de uma renovação real pelo
      Certbot central.
