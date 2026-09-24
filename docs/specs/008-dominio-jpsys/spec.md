# 008 — Domínio passa a ser jpsys.duckdns.org

## Comportamento
- O endereço da loja passa a ser `https://jpsys.duckdns.org/jalapao-store`. O domínio
  anterior, `jalapao-store.duckdns.org`, deixou de existir no DuckDNS em 24/09/2026 — a loja
  parou de responder por nome e só o IP seguia funcionando.
- O prefixo `/jalapao-store` continua. O domínio é genérico de propósito: pode servir outros
  projetos da VPS, cada um no seu caminho.
- O acesso por IP, `https://217.216.82.25/jalapao-store`, segue funcionando como antes.
- Os retornos OAuth do Mercado Livre e da Shopee passam para o domínio novo.

## Não objetivos
- Tirar o `/jalapao-store` do endereço. Está embutido no `basePath` do Next, nas rotas do
  Nginx, no admin e nos estáticos do Django e nos cookies — é mudança própria, não troca de
  nome.
- Mexer no certificado do IP ou no Certbot.

## Aceitação
`https://jpsys.duckdns.org/jalapao-store/login` responde 200 com certificado válido para o
nome, emitido pelo Traefik, sem `-k`. O manual em PDF responde pelo domínio novo. O IP segue
respondendo. Os dois deploys passam.
