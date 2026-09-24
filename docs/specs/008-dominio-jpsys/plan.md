# Plano

Troca literal do nome nos lugares onde ele é configuração, nos dois repositórios:

| Onde | O quê |
|---|---|
| `docker-compose.deploy.yml` | `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `APP_ORIGIN`, padrões de `ML_REDIRECT_URI` e `SHOPEE_REDIRECT_URI`, regra `Host()` da rota HTTPS no Traefik |
| `.github/workflows/deploy.yml` da loja | retornos gravados no `.env.marketplace` |
| `infra/deploy.sh` | checagens de `curl` do fim do deploy; caminho de reserva do Certbot via Nginx |
| `infra/nginx/https.conf` | `server_name` e certificado do caminho de reserva (`nginx-https`) |
| `.github/workflows/deploy.yml` do traefikproxy | host que o deploy valida |

O certificado não precisa de passo nenhum: o resolver ACME do Traefik emite para o nome
novo quando a rota aparece.

**Uma armadilha nisso:** entre a rota aparecer e o certificado sair, o Traefik entrega o
certificado padrão — o do IP — para o nome novo. O `curl` do fim do deploy falharia na
verificação, e `--retry` não repete erro de certificado. A checagem do domínio passou a usar
`--retry 20 --retry-delay 3 --retry-all-errors`.

Ordem: a loja primeiro, porque é ela que cria a rota que faz o Traefik pedir o certificado;
o traefikproxy depois, porque o deploy dele valida o domínio.
