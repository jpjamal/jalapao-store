# Plano

Três repositórios, e a ordem de publicação importa: **traefikproxy → jalapao-store →
Vinculus**. O `deploy.sh` da loja recusa rodar se faltar algo da infraestrutura central.

## traefikproxy
- `dynamic.yml` ganha o middleware `redirect-to-https`, usado por todos os sistemas.
- Serviço `certbot` (imagem oficial, `v5.4.0`): a cada 12 h renova o certificado do IP (ou
  emite, se não houver) em modo standalone, toca `traefik/dynamic.yml` para o Traefik reler a
  chave e deixa `publico/cert.pem` legível para o painel da loja. O router `acme-ip` leva
  `/.well-known/acme-challenge/` do IP até ele.
- O deploy copia `jalapao-store_certificates` para `infra_certificates` só na primeira vez e,
  no fim, testa a renovação de ponta a ponta com `certbot renew --dry-run` (ambiente de teste
  do Let's Encrypt, sem gastar cota).

## jalapao-store
- `docker-compose.deploy.yml` reescrito: sem `gateway`, `tls` e `certbot`; labels do Traefik
  no front (rotas normais, callback, HTTP) e no backend (só o Admin).
- `infra/deploy.sh`: confere rede e volume centrais antes de parar qualquer coisa; faz a troca
  de nome dos serviços (para os containers antigos, faz o backup a partir de qualquer dos dois
  nomes do banco); confere as rotas pelo caminho real, esperando o código certo (o Traefik leva
  alguns segundos para ler labels novos e, até lá, responde 404).
- Cópia local: o gateway passa a ser um Traefik com provedor de arquivo
  (`infra/traefik/local.yml`) — a mesma forma de rotear da produção.
- Saem `infra/nginx/` e `infra/renew-nginx.sh`.

## Armadilha evitada
`/jalapao-store/backend-api/products/` (com barra) recebe 308 do Next antes do 404. A
conferência usa o caminho sem barra.
