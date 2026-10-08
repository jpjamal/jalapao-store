# Validação

## Automatizada

- Backend completo no PostgreSQL 17 temporário e isolado: 324 testes aprovados, 5 ignorados por
  dependerem de serviços externos. A mesma suíte rápida no SQLite também foi aprovada.
- Casos novos: correção antes e depois do recebimento; diferenças positivas e negativas no Caixa;
  custo e estoque preservados na edição; cancelamento após várias correções; repetição segura;
  versão desatualizada; campos proibidos; permissões; exclusão repetida; devolução de produto e
  insumo; ocultação da lista; origem do Mercado Livre preservada; migração dos pedidos existentes.
- Ruff, `makemigrations --check` e validação do contrato OpenAPI aprovados.
- Frontend: `npm run typecheck` e `npm run build` aprovados, com todas as 20 rotas geradas.

## Interface

Conferência local em banco temporário: a lista mostrou os botões Editar e Excluir; o editor abriu
em janela flutuante com canal, referência, preços, desconto, taxas e frete preenchidos. O texto
explicou que produtos, quantidades e insumos são mantidos. A confirmação de exclusão reaproveita o
`ConfirmDialog` já usado no sistema e o fluxo foi coberto pela API automatizada.

## Publicação

Commit funcional `ae21021` criado por `jpjamal <jpfisica3@gmail.com>`, sem coautor. Workflow
GitHub Actions `37788728317` concluído com sucesso em 08/10/2026; testes, PostgreSQL/Next.js,
build e deploy passaram. Smoke check público: login e manifesto responderam HTTP 200.
