# Plano

> Etapas 1, 2 e 3 implementadas. Ver a [spec](spec.md).

**Contexto novo: `supplies`** (insumos), app Django com as mesmas camadas dos demais
(`domain/`, `models.py`, `services.py`, `api/`, `tests/`), e `features/supplies` no frontend.
Não entra em `catalog`, para o insumo não herdar telas e regras de venda.

**Modelos**
- `SupplyCategory(Entity)`: `name` (único sem diferenciar maiúscula, com `casefold()` no serializer
  como nas categorias de produto), `is_filament`, `active`. Separada de `catalog.Category`. A
  migração cria Filamentos (com `is_filament`), Embalagens, Colas e fitas, Acabamento, Ferramentas e
  Outros. `is_filament` não muda depois que a categoria tem insumos.
- `Supply(Entity)`: `category` (`PROTECT`), `name`, `unit` (texto), `notes`, `active`. Só para
  categoria de filamento: `material`, `color`, `roll_weight_g`, `roll_price`, exigidos pelo
  serializer conforme a categoria. Nome único dentro da categoria. `price_per_gram` e
  `price_per_kg` são propriedades calculadas em `Decimal`, sem arredondar o preço por grama.
- `SupplyStock`: um por insumo, `quantity` inteira não negativa e `version`, com `select_for_update`
  como o `Stock` dos produtos.
- `SupplyMovement`: razão imutável (`delta`, `balance_after`, `reason`, `actor`, vínculo opcional
  com a compra e vínculo opcional com a venda, que fica sem uso até a etapa 3), sem delete.
- `SupplyReceipt`: compra (insumo, quantidade, custo unitário, total, data, fornecedor,
  referência, `idempotency_key`, `request_hash`, `paid_at`, `status`, `cancelled_at`,
  `previous_roll_price`, `actor`), no molde do `Receipt`.

**Regras puras** em `domain/`: preço por kg a partir do rolo e validação dos campos por tipo.

**Serviços** (`services.py`, todos em `transaction.atomic`): `adjust_supply_stock` (única porta
de escrita do saldo), `create_supply_receipt` (entra no saldo; para filamento atualiza
`roll_price`) `pay_supply_receipt` (uma única saída no caixa) e `cancel_supply_receipt` (mesma regra da 023: só se
for a última movimentação do insumo; devolve o saldo, estorna o caixa se pago e restaura o preço do
rolo só se ele ainda for o da compra).

**Caixa**: `CashEntry` ganha `supply_receipt` (pagamento) e `refund_of_supply_receipt` (estorno),
ligações próprias e únicas, e a restrição de origem única passa a cobrir os vínculos de venda,
compra de produto e compra de insumo. Migração em `finance`.

**Peça 3D multicolor**: nova tabela `PrintingFilament` (perfil, filamento `PROTECT`, `grams`, e o
`roll_price` e o `roll_weight_g` do filamento copiados na hora de salvar). Guardar o preço e o peso
do rolo, e não o preço por grama, evita perder precisão: o custo da linha é uma única divisão,
`gramas × preço do rolo ÷ peso do rolo`. O serializer do produto aceita a lista de linhas, valida (1 a 8, sem repetir, gramas
positivas, só filamento, ativo ou já usado pela peça) e grava dentro da mesma transação. Com
linhas, `PrintingProfile.weight_g` passa a ser a soma das gramas e o custo do filamento vem de
`domain/pricing.py`, que ganha `filament_cost`, uma função pura que soma as linhas e deixa o
arredondamento para o total; sem linhas, a conta atual (`filament_price_kg` e `weight_g`) segue intacta. Um campo de
leitura por linha, `price_outdated`, compara o valor guardado com o atual.

**Ferramenta de custo 3D**: `features/tools/lib/custo3d.ts` ganha a mesma soma por linha. A
equivalência com o backend é garantida por testes com os mesmos casos numéricos nos dois lados
(a regra do projeto é que as duas contas deem o mesmo número).

**API** (`/api/v1/`): `supply-categories/` (listar, ver, criar, alterar), `supplies/` (listar, ver,
criar, alterar; filtros por categoria e situação; busca), `supply-receipts/` (listar, criar, `pay`,
`cancel`), `supply-movements/` (listar, criar baixa ou ajuste). Sem DELETE. Rotas novas entram na lista do BFF.

**Frontend**: `features/supplies/` com a tela de duas abas (com o painel "Gerenciar categorias" na primeira), menu "Insumos", e, no formulário do
produto 3D e na ferramenta, a lista de linhas (filamento e gramas) com o aviso de preço
desatualizado.

**Migrações**: `supplies 0001`, `catalog` (linhas de filamento do perfil) e `finance` (vínculo do caixa).
Nada do que existe é alterado ou apagado; peças atuais ficam sem filamento escolhido.

**Etapa 3 — insumos na venda.** `SaleSupply` (app `supplies`, ligado a `sales.Sale` por chave de texto,
como `SupplyMovement.sale`): `sale`, `supply`, `supply_name`, `requested` e `taken`, único por venda e
insumo, com `taken ≤ requested`. Guarda o que foi pedido e o que de fato foi baixado, porque falta de
saldo não impede a venda. `consume_supplies_for_sale` (em `supplies/services.py`) roda dentro do
`create_sale`: trava os insumos em ordem de id (evita impasse), baixa `min(pedido, saldo)` por
`adjust_supply_stock`, com a movimentação ligada à venda, e grava o `SaleSupply`.
`restore_supplies_for_sale` roda no `cancel_sale` e devolve só `taken`, com `allow_inactive` para
insumo que foi desativado depois. O `SaleInput` ganha `supplies` opcional; a resposta traz, por linha,
`requested`, `taken` e `shortfall`. Quem informa insumos (e quem cancela uma venda que baixou) precisa
da permissão de movimentar o estoque de insumos. O importador do Mercado Livre não envia `supplies` e
portanto não baixa nada. O custo e o lucro da venda não mudam: o cálculo nem lê os insumos. Migração
`supplies 0003`; frontend: seção "Insumos usados" em Vendas, aviso do que faltou e os insumos no
histórico.
