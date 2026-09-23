# Compras e produção

Fonte funcional: ../../../docs/specs/002-stock-cost/spec.md.
Menu Compras / produção → /entradas, um produto por entrada. Custo sugerido ao escolher
produto, livre para informar custo real. Total no navegador é prévia; backend calcula.
Validações numéricas e data, erros da API visíveis, botão bloqueado durante envio,
idempotency_key mantida em retry e renovada após sucesso. Histórico paginado preservado.

Pagamento pede data e confirmação do total, com alerta de duplicidade manual. Produção
não oferece pagamento. Estoque usa stock_value/average_cost do backend; ajustes positivos
exigem custo. Caixa identifica a origem Compra de estoque. Catálogo exibe Custo de referência.
