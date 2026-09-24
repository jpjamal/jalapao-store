# Validação local — 2026-09-23

- `manage.py check`: sem problemas.
- `makemigrations --check --dry-run`: sem mudanças faltantes.
- Testes de integração Mercado Livre: 9 passaram, com transporte falso, sem rede.
- Suíte Django completa: 61 testes, 52 passaram e 9 foram ignorados por exigirem PostgreSQL (execução local com SQLite).
- `npm run build`: compilação e TypeScript passaram.
- Nenhum commit, push, deploy, acesso à VPS ou chamada real ao Mercado Livre.

## Não validado

O DevCenter ainda precisa confirmar o URI de retorno HTTPS (inclusive se aceita o IP da VPS), PKCE da aplicação, escopos e credenciais. A resposta de uma conta real, estoque Full/depósitos e limites de chamada precisam de teste controlado antes de habilitar envio em produção. A proteção posterior dos tokens está na spec 007.

Referências oficiais: [OAuth](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao), [itens e buscas](https://developers.mercadolivre.com.br/itens-e-buscas), [estoque multiorigem](https://developers.mercadolivre.com.br/pt_br/estoque-multi-origem).
