# Plano

Adicionar `counts_as_expense_snapshot` a `SupplyReceipt`. O serviço de compra copia o valor da categoria
dentro da mesma transação; a API o expõe somente para leitura e a lista de compras apresenta a regra.

A migração adiciona o campo temporariamente anulável, copia para cada compra existente a configuração
atual da categoria e depois torna o campo obrigatório. `supply_expense` passa a somar pagamentos e
estornos pelo snapshot da compra, sem seguir a categoria atual do insumo.

Cobrir mudança da opção, troca de categoria, compra futura, estorno e preenchimento da migração. Rodar
suíte completa em PostgreSQL 17, lint, migrações, OpenAPI, typecheck e build.
