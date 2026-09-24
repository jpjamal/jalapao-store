# Validação local — 2026-09-23

- `manage.py check`: sem problemas.
- `makemigrations --check --dry-run`: sem mudanças faltantes.
- Testes de integração Mercado Livre: 9 passaram, com transporte falso, sem rede.
- Suíte Django completa: 61 testes, 52 passaram e 9 foram ignorados por exigirem PostgreSQL (execução local com SQLite).
- `npm run build`: compilação e TypeScript passaram.
- Nenhum commit, push, deploy, acesso à VPS ou chamada real ao Mercado Livre.

## Não validado em 2026-09-23

Naquela data, o DevCenter ainda precisava confirmar o URI de retorno HTTPS, PKCE da aplicação, escopos e credenciais. A resposta de uma conta real, estoque Full/depósitos e limites de chamada precisavam de teste controlado antes de habilitar envio em produção. A proteção posterior dos tokens foi tratada na spec 007.

Referências oficiais: [OAuth](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao), [itens e buscas](https://developers.mercadolivre.com.br/itens-e-buscas), [estoque multiorigem](https://developers.mercadolivre.com.br/pt_br/estoque-multi-origem).

## Teste com a API real — 2026-09-24

- Conta conectada na VPS: usuário `96417426`, ativa, token válido no início do teste e sem erro registrado.
- Consulta autenticada de `/users/{user_id}`: ID da resposta corresponde à conta, site `MLB` e estado `active`.
- Consulta autenticada de `/users/{user_id}/items/search?limit=5&offset=0`: HTTP 200, `paging.total = 0`, sem anúncios na página.
- Fluxo `importar_anuncios`: total remoto 0, vínculos novos 0, pendências 0; vínculos locais dessa conta permaneceram em 0. A data da última sincronização foi registrada.
- Suíte local `apps.common.test_mercado_livre`: 9 testes passaram usando banco de teste SQLite e transporte falso.
- Nenhum anúncio foi publicado ou modificado; nenhum estoque foi enviado ao Mercado Livre. Não foi possível exercitar o vínculo por SKU, os detalhes de anúncios ou o envio de estoque sem um anúncio real na conta.
