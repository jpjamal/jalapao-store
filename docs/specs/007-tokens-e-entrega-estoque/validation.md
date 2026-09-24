# Validação local — 2026-09-23

- Suíte completa com PostgreSQL 17 local: **75 testes passaram**. Inclui teste com duas solicitações concorrentes para o mesmo anúncio, regressões Shopee/Mercado Livre e conversão de tokens legados.
- SQLite local: 75 testes, 65 passaram e 10 foram ignorados por exigirem PostgreSQL. A fonte principal desta spec é a suíte PostgreSQL acima.
- `ruff check` nos módulos alterados: sem erros.
- `manage.py check` e `makemigrations --check --dry-run`: sem problemas.
- Contrato OpenAPI gerado com `--validate --fail-on-warn`: sem avisos.
- `uv.lock` atualizado com `cryptography==50.0.1`. Instalação de desenvolvimento apenas no ambiente virtual local. Construção da imagem de teste local passou.
- Nenhum commit, push, deploy, acesso à VPS ou mudança no banco de uso local. A suíte usou `test_jalapao`, que foi removido ao fim.

## Limites

Não houve acesso a contas reais de marketplace. O valor de `DJANGO_SECRET_KEY` precisa ser preservado: a chave dos tokens deriva dele. Backups anteriores à migração podem ainda conter texto claro e devem continuar sob acesso restrito. A migração de dados foi testada com valores legados simulados; a execução contra dados reais de produção permanece pendente de uma publicação futura autorizada.
