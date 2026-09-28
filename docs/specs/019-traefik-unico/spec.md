# 019 — Traefik como único proxy

Até aqui eram dois proxies em fila: o Traefik central (traefikproxy) terminava o HTTPS e
entregava tudo a um Nginx da loja, que repartia entre front, backend, manuais e o desafio
ACME do IP. O dono quer **um** lugar para tudo o que é infraestrutura — o traefikproxy, que já
traz o Portainer. Os sistemas só declaram as próprias rotas, em labels do compose de deploy.

## Comportamento
- A loja não tem Nginx nem Certbot. O Traefik roteia direto para os containers dela.
- **Só o front na internet.** O navegador fala com o Next; o BFF chama o Django pela rede
  interna do Docker (`http://jalapao-backend:8000`). A API não tem rota pública — a rota
  `/jalapao-store/backend-api/` deixa de existir; a documentação da API fica para o ambiente
  local.
- Exceção aceita: o **Django Admin** (`/jalapao-store/admin/` e os estáticos dele,
  `/jalapao-store/django-static/`), com router próprio de prioridade maior.
- O retorno da autorização (`/jalapao-store/callback`) mantém `Referrer-Policy: no-referrer`.
- HTTP redireciona para HTTPS pelo middleware central `redirect-to-https@file`; os cabeçalhos
  de segurança vêm de `secure-headers@file`. Envio de foto continua limitado a 11 MB.
- O certificado do IP passa a ser emitido por um **Certbot central** no traefikproxy (o
  Traefik v3.6 ainda não emite certificado para IP), em modo standalone. O volume antigo da
  loja é copiado uma vez para `infra_certificates`: mesma conta ACME, sem reemitir.
- Os serviços ganham nomes únicos (`jalapao-db`, `jalapao-backend`, `jalapao-frontend`): a rede
  `traefik_proxy` é dividida com outros sistemas, e um `backend` genérico responderia por outro.
- Os manuais em PDF (`/manuais/`) saíam de uma pasta servida pelo Nginx. Passam para o
  servidor de arquivos — ver [spec 020](../020-servidor-de-arquivos/spec.md).

## Não objetivos
- Não mudar a aplicação: telas, API e dados ficam iguais.
- Não mexer nas rotas dos outros sistemas além do necessário (o Vinculus faz a mesma
  mudança na spec 017 dele).

## Aceitação
Pelo domínio e pelo IP: login 200, Django Admin 200, `/jalapao-store/backend-api/...` 404,
HTTP 301 para HTTPS, cabeçalhos de segurança presentes, `no-referrer` no callback e envio
acima de 11 MB recusado com 413. Nenhum container da loja publica porta no host.
