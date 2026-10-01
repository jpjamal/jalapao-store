# Plano

`DashboardView` (`apps/common/api/views.py`) ganha `realized_profit`: a mesma soma do campo `profit` que já
existe nas vendas, filtrando `status="confirmed"` e `received_at` não nulo. Nenhum modelo, migração ou
cálculo de venda muda. O contrato OpenAPI ganha o campo.

No frontend, o cartão "Lucro estimado" vira "Lucro previsto" e ao lado entra "Lucro real", cada um com a
explicação do que conta.
