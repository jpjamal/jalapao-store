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

## Produção (28/09/2026)
- traefikproxy `49db723` publicado: Traefik recriado, certbot central rodando com o certificado
  copiado do volume da loja (mesma linhagem `jalapao-ip`, válido até 04/10/2026).
- **Renovação provada de ponta a ponta:** o `certbot renew --dry-run` do deploy recebeu o
  desafio HTTP-01 do IP pelo Traefik (router `acme-ip`) e validou no ambiente de teste do Let's
  Encrypt. Fora de um terminal o certbot espera até ~5 min aleatórios antes de renovar; é normal
  o passo demorar.
- Loja `bed6a6c` publicada: containers com nome novo saudáveis; `gateway`, `tls` e `certbot`
  removidos. Pelos dois hosts: login 200, Admin 200, `backend-api` 404, manifesto 200,
  `no-referrer` no callback, HTTP 301 para HTTPS.

## Primeira renovação real (01/10/2026)
- O certbot central renovou o certificado do IP sozinho às 02:51 UTC (`cert3.pem`, válido até
  07/10/2026), e o Traefik passou a servir o novo sem intervenção: o aviso pelo `touch` do
  `dynamic.yml` funciona. Era a pendência aberta desde 24/09 (spec 018).
