# Plano

**Backend**
- `supplies/models.py`: `Supply.unit_cost`; `SupplyStock.uncosted` (com restrição `uncosted ≤ quantity`);
  `SupplyReceipt.previous_unit_cost`; `SupplyMovement.unit_cost`; `SaleSupply.zero_cost_qty`, `unit_cost`,
  `cost_total`; modelo novo `ProductSupply` (embalagem padrão, no app de insumos para não criar import circular com o
  catálogo). Migrações `supplies/0006` (estrutura) e `0007` (dados: saldo atual sem custo, custo da última compra,
  Embalagens sem despesa); `sales/0007` (`Sale.supplies_cost`).
- `supplies/services.py`: `adjust_supply_stock` ganha `uncosted` (padrão: entrada sem custo, saída consome a parte sem
  custo primeiro) e `unit_cost`; `register_supply_adjustment` (baixa/ajuste à mão, com custo opcional na entrada);
  compra e cancelamento mantêm o custo e a parte sem custo; `consume_supplies_for_sale` congela o custo por linha;
  `restore_supplies_for_sale` devolve a parte sem custo; `set_product_supplies`.
- `sales/services.py`: `create_sale` grava `supplies_cost` e desconta do lucro; `edit_sale` mantém o desconto;
  `_snapshot` inclui o campo.
- API: insumo expõe `unit_cost` (só leitura) e `uncosted`; movimento aceita `unit_cost`; produto ganha
  `default_supplies`; linha de insumo da venda expõe o custo; ordenação por `unit_cost`.

**Frontend**
- Insumos: coluna "Custo unitário", "N sem custo" sob o saldo, detalhes na janela, custo opcional no ajuste.
- Produtos: componente `default-supplies.tsx` no formulário e "Embalagem padrão" na janela.
- Vendas: `kitFor` preenche os insumos pela embalagem padrão enquanto não forem editados; `supplyCost` estima o custo;
  janela da venda mostra o custo das embalagens e de cada linha.

**Por que "último custo" e "parte sem custo"**: é o mesmo modelo do filamento (último preço pago) e evita contar duas
vezes o que já entrou como despesa, sem precisar de camadas de custo por compra.
