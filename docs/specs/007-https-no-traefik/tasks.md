# Tarefas

- [x] Entrypoint `websecure`, resolver ACME do DuckDNS e `acme.json` persistente.
- [x] Certificado do IP como padrão do Traefik, lido do volume compartilhado.
- [x] Porta HTTPS por variável, com pré-validação no loopback.
- [x] Workflow do Traefik descobre a porta e valida os dois certificados.
- [x] Gateway da loja serve a aplicação em HTTP na 8080 para o Traefik.
- [x] Nginx TLS movido para o perfil `nginx-https`.
- [x] Detecção exata de quem publica a 443, sem o falso positivo do `8443`.
- [x] Certbot avisa o Traefik por bind mount de diretório, com guarda no deploy.
- [x] `JALAPAO_TLS` decide quem termina TLS; a loja recusa configuração inconsistente.
- [x] Traefik recusa assumir a 443 ocupada, e nesse caso nem é recriado.
- [x] Passo de deploy do Traefik reconstruído e conferido (YAML, escape do heredoc, `bash -n`).
- [ ] Publicar a loja, publicar o Traefik em pré-validação e conferir os certificados.
- [ ] Virada da porta 443 e remoção do `tls` do ar.
- [ ] Apagar o certificado órfão `jalapao-domain` (sslip.io), que ninguém usa.
