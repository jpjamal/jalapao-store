# Validação

## Ensaio local (28/09/2026)
Traefik v3.6 com cópia do `traefik.yml` e do `dynamic.yml` de produção (resolver ACME
apontado para endereço inválido, para não emitir nada), rede `traefik_proxy` e volume
`infra_certificates` com certificado autoassinado; a loja com o `docker-compose.deploy.yml`
novo, imagens construídas do código.

Nos dois hosts (domínio e IP, por `--resolve`):

| Checagem | Resultado |
|---|---|
| `/jalapao-store/login` | 200 |
| `/jalapao-store/admin/login/` | 200 |
| `/jalapao-store/django-static/…` | 200 |
| `/jalapao-store/backend-api/products` | 404 (sem rota pública) |
| `/jalapao-store/manifest.webmanifest` | 200 |
| `http://…/jalapao-store/login` | 301 para HTTPS |
| Cabeçalhos | `nosniff`, `SAMEORIGIN`, `strict-origin-when-cross-origin` |
| `/jalapao-store/callback` | `Referrer-Policy: no-referrer` |
| Envio de 12 MB | 413 |
| Certificado pelo IP | o padrão (`tls.stores.default`) |

## Limites da evidência
O Certbot em modo standalone não dá para ensaiar sem o IP público; quem prova a renovação é
o `certbot renew --dry-run` do deploy do traefikproxy.
