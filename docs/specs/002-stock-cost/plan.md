# Plano

Receipt no domínio inventory com FK PROTECT para produto/autor; Movement aponta Receipt.
Stock.value armazena avaliação e average_cost é derivado. Movement guarda variação e saldo
monetários. SaleItem.cost_total congela baixa exata; unit_cost mantém apresentação do snapshot.
CashEntry.receipt relaciona pagamento único à compra. Serviços atômicos, bloqueio de produto
e chave idempotente PostgreSQL. Migração de dados antes de uso dos novos campos.

DRF receipts GET/POST e receipts/{id}/pay POST; BFF permite rotas. Tela Entradas com formulário,
histórico paginado e pagamento explícito. Estoque/painel exibem valor persistido; catálogo
distingue referência da média. Contrato OpenAPI e READMEs atualizados.
