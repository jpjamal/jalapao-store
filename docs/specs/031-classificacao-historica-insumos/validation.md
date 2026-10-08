# Validação

## Automatizada

- Suíte completa no PostgreSQL 17 temporário e isolado: **326 testes aprovados**, 5 ignorados por
  dependerem de serviços externos.
- Casos específicos aprovados: regra ligada e desligada; compra não paga; mudança posterior da opção;
  troca de categoria; compra futura; pagamento; estorno após troca de categoria; preenchimento das
  compras antigas pela migração; campo somente leitura na API.
- Migração aplicada desde banco vazio e `makemigrations --check` sem alterações pendentes.
- Ruff aprovado; contrato OpenAPI regenerado e validado sem avisos.
- Frontend: `npm run typecheck` e `npm run build` aprovados, com todas as 20 rotas geradas.

## Compatibilidade dos dados

A migração copia para cada compra existente a opção atual de sua categoria e não modifica valores,
pagamentos, Caixa ou estoque. Após a migração, a classificação de cada compra deixa de acompanhar
mudanças no cadastro.

## Publicação

Commit funcional `d22ee66` criado por `jpjamal <jpfisica3@gmail.com>`, sem coautor. Workflow GitHub
Actions `37850459154` concluído com sucesso em 08/10/2026; testes, PostgreSQL/Next.js, build e deploy
passaram. Smoke check público: login e manifesto responderam HTTP 200.
