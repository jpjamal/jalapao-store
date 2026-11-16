# Plano

**Backend**
- `catalog/models.py`: modelo novo `PrintingComponent` (perfil 3D, insumo, quantidade, custo unitário copiado,
  posição); `PrintingProfile.prices()` soma os componentes. `catalog/domain/pricing.py`: `components_cost` e o
  parâmetro `component_lines` em `printing_cost`. Migração `catalog/0009`.
- `catalog/api/serializers.py`: `PrintingComponentSerializer` (recusa filamento; `price_outdated`; `refresh_price`),
  `PrintingSerializer.components` (máximo 20, sem repetir, inativo só se já estava); `_save_components` copia o custo
  do insumo em linha nova ou quando pedido. View prefetch de `printing__components__supply`.
- `supplies/models.py`: `ProductionSupply` (produção, insumo, unidade, pedido, baixado, parte sem custo) e
  `SupplyMovement.production`. Migrações `supplies/0008` (estrutura) e `0009` (dados: filamento em gramas, unidade
  "g", categoria Componentes).
- `supplies/services.py`: `roll_grams`; compra de filamento entra em gramas; cancelamento tira o `delta` do
  movimento da compra; ajuste de filamento recusa custo; venda recusa filamento; `production_requirements`,
  `consume_supplies_for_production`, `restore_supplies_for_production`.
- `inventory/services.py`: `create_receipt` aceita `consume_supplies` e, na produção, chama a baixa;
  `cancel_receipt` devolve os insumos. API: `ReceiptInput.consume_supplies` (padrão ligado) e
  `ReceiptSerializer.supply_lines`.
- `supplies/api/serializers.py`: cadastro de filamento grava unidade "g".

**Frontend**
- `features/tools/lib/custo3d.ts`: `componentes` na conta.
- `features/catalog/components/component-lines.tsx` (novo): editor de componentes, usado em Produtos e na ferramenta.
- `features/catalog/products-page.tsx`: componentes no formulário; "Composição da peça" na janela do produto.
- `features/tools/printing-cost-page.tsx`: componentes e a linha "Componentes" no resultado.
- `features/inventory/receipts-page.tsx`: prévia do que a produção vai tirar, opção de não baixar, aviso do que saiu
  e do que faltou, "Insumos usados" na janela, aviso no cancelamento.
- `features/supplies/format.ts` (novo): saldo em gramas com "≈ N rolos"; Insumos e a ação mostram gramas; compra de
  filamento em rolos; unidade do filamento fixa.
- `features/sales/sales-page.tsx`: lista de insumos da venda sem filamento.
