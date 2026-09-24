# Validação

Em 2026-09-23:
- SQLite local: 22 testes encontrados, 18 passaram, 4 de concorrência aguardam PostgreSQL CI.
- Ruff e contrato OpenAPI sem avisos; migrations detectadas e aplicadas no banco local.
- Build Next.js e TypeScript passaram.
- Navegador local: compra de 10 un. a R$14, pagamento de R$140, produção de 2 un. a R$20.
  Saldo anterior de teste: 3 un. / R$30. Resultado: 15 un. / R$210 / média R$14;
  produção sem saída automática e compra identificada como paga. Sem transações de teste na VPS.
- Teste de migração: estoque anterior recebe avaliação inicial e venda mantém lucro e snapshot.

Publicação e testes concorrentes em PostgreSQL ainda pendentes nesta revisão.

Segunda revisão, ainda em 2026-09-23 — a publicação havia falhado:
- O job `quality` terminou com exit 1, então `build` e `deploy` nem chegaram a rodar. A produção
  permaneceu em `inventory.0001_initial`, sem a tabela de entradas.
- Causa: as threads dos testes de concorrência encerravam com `close_old_connections()`, que não
  fecha conexão recente enquanto o `CONN_MAX_AGE` de 60s a considera viva. As threads morriam com
  a conexão aberta e o `destroy_test_db` do fim da suíte esbarrava em
  `database "test_jalapao" is being accessed by other users`. Os 22 testes passavam; quem
  devolvia erro era o encerramento.
- Correção: cada thread fecha a própria conexão com `connection.close()` no `finally`.
- Reprodução em PostgreSQL 17 real: antes da correção, 22 testes OK e falha no teardown; depois,
  o job inteiro passa — ruff, check, makemigrations, contrato OpenAPI e os 22 testes, incluindo
  os 4 de concorrência que só rodam em PostgreSQL.

- Publicado em seguida por `7d3d234`, com o deploy concluído. Conferido no banco de produção:
  `inventory -> 0003_opening_stock_value`, `sales -> 0003_historical_item_cost` e
  `finance -> 0002_cashentry_receipt_cashentry_cash_single_origin` aplicadas, e a tabela
  `inventory_receipt` existindo com zero registros — nenhuma transação fictícia foi criada
  na produção. Os seis containers voltaram `healthy` e as rotas HTTPS seguiram respondendo.
