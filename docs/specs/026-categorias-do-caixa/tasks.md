# Tarefas

> Implementada; falta só publicar.

- [x] Aprovação do dono e decisões fechadas da [spec](spec.md).
- [x] `SupplyCategory.counts_as_expense` (migração com os valores iniciais), na API e na tela de insumos.
- [x] `CashCategory`, `CashEntry.category`, categoria automática pela origem no `save()` e migração com as
      categorias do sistema, as iniciais e a classificação dos lançamentos existentes.
- [x] API: `cash-categories/`, categoria no `cash/` (criar e reclassificar), `origin`, resumo por categoria e
      contrato OpenAPI.
- [x] Painel: `business_result` e `unclassified_count`.
- [x] Frontend: categoria no formulário, coluna e filtro, resumo por categoria, gerenciar categorias, coluna
      Origem corrigida e o cartão Resultado do negócio com o aviso de lançamentos a classificar.
- [x] Testes, documentação (arquitetura, guia do Caixa, READMEs) e validação com PostgreSQL.
- [ ] Publicação pelo GitHub (só quando o dono mandar).
