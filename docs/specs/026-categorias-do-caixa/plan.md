# Plano

> Aprovada; ver a [spec](spec.md).

**Modelo.** `CashCategory(Entity)` no app `finance`: `name` (único sem diferenciar maiúscula, com `casefold()`
no serializer, como nas outras categorias), `direction` (entrada, saída, ambas), `counts_in_result`, `active`
e `system_key` (texto único e opcional; só as categorias do sistema o têm, e é por ele, e não pelo nome, que o
código as encontra, para renomear não quebrar nada). `CashEntry.category` é chave estrangeira `PROTECT`.

**Categoria automática pela origem.** O `save()` do `CashEntry` preenche a categoria do sistema quando ela
falta, pelas ligações que o lançamento já tem (`sale`, `receipt`, `supply_receipt` e os estornos
`refund_of_receipt` e `refund_of_supply_receipt`), no mesmo estilo do SKU e da categoria padrão do produto.
Assim todo caminho que cria lançamento (venda, compra, insumo, estorno, API) fica coberto sem mexer nos
serviços. Lançamento sem origem e sem categoria é recusado pela API; no código vai para **A classificar**.

**Migração.** Cria as categorias do sistema e as iniciais do dono; liga cada lançamento existente pela origem
e leva os manuais para **A classificar**. A categoria passa a ser obrigatória no banco depois disso. Os nomes
ficam escritos na migração, que não depende do código do app.

**API.** `cash-categories/` (listar, ver, criar, alterar; filtros por direção, ativa e sistema; sem DELETE;
categoria do sistema só leitura). `cash/` aceita `category` na criação, valida a direção e que não seja do
sistema, e ganha `PATCH` que **só** altera `category` de lançamento manual (qualquer outro campo é recusado),
com `change_cashentry`. A resposta traz `category_name` e `origin` (venda, compra de produto, compra de
insumo, estorno ou manual). Um resumo por categoria (`cash/summary/`) soma entradas e saídas.

**Resultado.** `DashboardView` ganha `business_result` e `unclassified_count`. O resultado é o lucro real mais
as entradas e menos as saídas dos lançamentos manuais cujas categorias têm `counts_in_result`, menos os
pagamentos de compra de insumo (e mais os estornos) **cuja categoria de insumo tem `counts_as_expense`**.
`SupplyCategory.counts_as_expense` é um campo novo (migração em `supplies`, com os valores iniciais da
spec); o cálculo olha a categoria do insumo na hora, então mudar a opção vale também para o passado.

**Frontend.** `features/finance/`: formulário com categoria, coluna e filtro, resumo por categoria e painel
**Gerenciar categorias** (como em Insumos); a coluna Origem usa o `origin` da API. Tela inicial: cartão
**Resultado do negócio** e aviso de lançamentos a classificar. Rotas novas na lista do BFF.
