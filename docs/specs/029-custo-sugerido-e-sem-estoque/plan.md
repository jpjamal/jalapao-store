# Plano

Só frontend.

- `features/inventory/stock-page.tsx`: o seletor de produto guarda o produto escolhido e preenche o custo com
  `cost_price`; o campo de custo vira controlado, com a linha que explica a origem do valor.
- `shared/components/stock-quantity.tsx`: `StockQuantity` (quantidade + selo) e `linhaDeEstoque` (classe da linha),
  usados em `features/catalog/products-page.tsx` e na posição do estoque.
- `app/globals.css`: `tr.sem-estoque` (fundo com 15% de `--destructive`, no computador e no cartão do celular) e
  `.selo-sem-estoque`.
- `features/catalog/components/product-picker.tsx`: "sem estoque" em vermelho no lugar de "0 un." nas opções.
