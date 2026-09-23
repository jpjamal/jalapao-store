# Contrato de custos e entradas

Fonte funcional: ../../../docs/specs/002-stock-cost/spec.md.
POST receipts: idempotency_key UUID, product_id UUID, kind purchase/production,
quantity 1..1000000, unit_cost decimal não negativo, occurred_on até hoje,
supplier/reference/notes opcionais. Retorna 201 com snapshot e total. Mesma chave com
outro conteúdo/autor retorna 400. Escrita bloqueia produto, soma valor e quantidade,
grava Movement e Outbox na mesma transação. Não altera cost_price do catálogo.

POST receipts/{id}/pay: occurred_on até hoje; compra somente. Pagamento idempotente total,
saída única no caixa, sem segunda alteração de estoque. GET exige view_receipt.
Histórico apenas leitura no Admin e API, sem PATCH/DELETE. OpenAPI em ../openapi.yml.

Migrações inicializam avaliação existente; movimentos históricos sem valor são null.
Backup e pausa da API antes de migrar evitam escritas com regra antiga durante o corte.
Não voltar a código anterior de custos após migrar sem restaurar backup consistente.
