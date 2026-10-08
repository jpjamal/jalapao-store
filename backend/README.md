# Backend Jalapão Store

Django 5.2 LTS, DRF, SimpleJWT, PostgreSQL 17, Python 3.13 na imagem.
Gerenciador: **uv**; dependências exatas em `uv.lock`. Nunca instalar no Python global.

## Desenvolvimento
Na pasta backend, `uv sync --frozen` cria `.venv`. Configurar DJANGO_SECRET_KEY,
POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_DB=jalapao e POSTGRES_USER=jalapao no ambiente.
Executar `uv run python manage.py migrate` e `uv run python manage.py runserver`.
Settings por ambiente em `config/settings/`: `production` é o padrão; para DEBUG local use
`DJANGO_SETTINGS_MODULE=config.settings.development`; os testes usam `config.settings.test`.
Banco isolado com backend/compose.yml (`docker compose --env-file ../.env up --build`).
Stack completa: compose da raiz. `.env.example` contém apenas valores de desenvolvimento.

`TEST_SQLITE=1` permite testes rápidos locais; não usar em produção. Concorrência é
testada somente em PostgreSQL no CI. Rodar
`DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py test apps` — os testes
ficam em `apps/<contexto>/tests/`.
Rodar `uv run ruff check . --exclude migrations` e `uv run python manage.py makemigrations --check`.

## Organização e contratos
Cada app é um contexto com as camadas `domain/` (regra pura), `models.py`, `services.py`
(casos de uso), `api/` (`serializers`, `permissions`, `views`, `urls`) e `tests/`. Mapa
completo e regras de dependência em [../docs/architecture.md](../docs/architecture.md).

- accounts: usuário Django extensível, grupos/permissões, JWT e bootstrap explícito.
- common: núcleo compartilhado — entidade base, `domain/money.py`, permissões, erros e painel.
- catalog: Category (spec 022) substitui o antigo `Product.kind`: `uses_printing_profile` diz
  que os produtos dela levam PrintingProfile. Sem DELETE, só `active`; a opção trava quando há
  produtos. Product tem `category` (PROTECT, obrigatória no banco), `brand`, `model` e
  `weight_g` (peso do produto, opcional). Sem categoria na API, entra a de produção 3D se vierem
  parâmetros 3D e a comum mais antiga se não (`default_category`/`printing_category`).
- supplies (spec 024, etapa 1): SupplyCategory e Supply, o cadastro de insumos, separado de produtos
  (insumo não tem SKU nem preço de venda e nunca aparece em vendas ou anúncios). Categoria com
  `is_filament` trava depois do primeiro insumo; insumo de filamento exige material, cor, peso e
  preço do rolo, e o preço por grama é `preço ÷ peso` sem arredondar (`domain/pricing.py`). Sem
  DELETE: desativa-se. Rotas `supply-categories/`, `supplies/` e `supplies/materials/`. Estoque,
  SupplyStock guarda só a quantidade (sem custo médio); SupplyReceipt é a compra
  (cancelável, sem apagar); SupplyMovement é o razão imutável. Todo saldo muda por `services.py`
  (`adjust_supply_stock`, `create_supply_receipt`, `pay_supply_receipt`, `cancel_supply_receipt`):
  compra entra na hora e fica a pagar; pagar gera uma saída no caixa (`CashEntry.supply_receipt`);
  cancelar só vale se for a última movimentação do insumo e estorna o caixa (`refund_of_supply_receipt`),
  devolvendo o preço do rolo se ele não foi editado. Rotas `supply-receipts/` (`pay`, `cancel`) e
  `supply-movements/` (baixa e ajuste). Etapa 3: a venda aceita `supplies` (`[{supply_id, quantity}]`);
  `consume_supplies_for_sale` baixa `min(pedido, saldo)` na mesma transação, grava `SaleSupply`
  (`requested`, `taken`) e liga a movimentação à venda; falta de saldo não impede a venda e aparece em
  `shortfall`; `cancel_sale` devolve só `taken`. Não mexe em custo nem lucro; o importador do Mercado
  Livre não envia insumos.
- catalog: peça 3D multicolor (spec 024): `PrintingFilament` liga o perfil a filamentos, com as
  gramas e o preço e peso do rolo copiados ao salvar; o custo do filamento é a soma
  `gramas × preço ÷ peso` por linha (`filament_cost`), arredondada só no total. Mudar o filamento
  depois não altera a peça: a API só marca `price_outdated`, e `refresh_price` traz o preço atual.
  Sem linhas vale a conta de sempre.
- catalog: Product e PrintingProfile 1:1; cálculos em `domain/pricing.py`, SKU em `domain/sku.py`.
- catalog: ProductImage guarda fotos privadas por produto; ListingDraft guarda conteúdo
  opcional por produto e canal, com ordem de fotos própria. Salvar não publica anúncio.
- Código de barras (spec 021): `Product.gtin` opcional e único (GTIN-8/12/13/14, com dígito
  verificador; regra em `domain/gtin.py`). Vazio é `NULL`; espaços e hífens são removidos ao
  salvar. `?search=` da API de produtos também procura pelo GTIN.
- Novos produtos recebem SKU automático `SKU-<iniciais>-<sequência>` (ex.: `SKU-LP-0001`).
  O número é global e crescente; estoque é um campo separado. SKUs existentes e importados
  permanecem intactos. A API expõe o SKU apenas para leitura.
- inventory: saldo 1:1, histórico N:1, serviços atômicos com bloqueio do produto.
- inventory.Receipt: compras/produções por produto com custo congelado; Stock.value mantém
  avaliação pelo custo médio móvel. Product.cost_price é apenas referência de novas entradas.
- sales: Sale 1:N SaleItem; snapshots, chave idempotente e cancelamento reversível. Spec 030:
  venda confirmada aceita correção de canal, referência e valores, mantendo produto, quantidade,
  custo e insumos. `SaleRevision` guarda autor e antes/depois. Venda recebida gera no Caixa somente
  a diferença da correção; a categoria automática não entra de novo no Resultado do negócio.
  Excluir é lógico (`deleted_at`): cancela e estorna uma vez, some da lista e preserva o histórico.
  `external_channel` mantém a origem importada mesmo quando o canal exibido é corrigido.
- Listagens (spec 027): os filtros de busca e de ordem são globais (`apps/common/filters.py`). Busca e ordem de
  texto ignoram acento e maiúscula por `Fold` (igual no PostgreSQL e no SQLite); cada view declara `search_fields`,
  `ordering_fields`, `ordering_text_fields` e `ordering_zero_fields`; `range_filterset` cria `date_from`/`date_to`.
  Lista nova: copie uma view existente e o `api/filters.py` do app.
- finance: entradas/saídas imutáveis. Recebimento e estorno por venda são únicos. Spec 026: todo
  lançamento tem `CashCategory` (direção, `counts_in_result`, ativa; categorias do sistema têm `system_key`
  e são só leitura). `CashEntry.save()` põe a categoria do sistema pela origem (`domain/categories.py`); o
  manual exige categoria de direção compatível pela API e depois só a categoria muda (PATCH). `cash/summary/`
  soma por categoria e `origin` diz de onde veio o lançamento. O Resultado do negócio (`services.py`, no
  painel como `business_result`) soma o lucro real, os manuais que contam e a despesa de insumos das
  categorias com `SupplyCategory.counts_as_expense`; `unclassified_count` avisa os "A classificar".
- integrations: Listing relaciona produto interno a item/user_product/family; outbox transacional.
  Tokens de marketplace são cifrados em repouso com chave derivada de DJANGO_SECRET_KEY;
  preserve esse segredo ao atualizar a instalação. Cada anúncio Shopee acompanha a versão
  de estoque enviada, para não encerrar eventos de outras contas nem reenviar saldo antigo.

App por domínio; ORM é persistência, services são casos de uso, api é camada HTTP.
integrations separa ainda `domain/ports.py` (contrato do adaptador), `infrastructure/`
(clientes HTTP do Mercado Livre e da Shopee, cifra dos tokens) e `services/`
(sincronização e os casos de uso do Mercado Livre: anúncio, publicação, pesquisa, pedidos).
Históricos usam PROTECT. Sem DELETE comercial. Desativar produtos pelo campo active.

API `/api/v1/`, só na rede interna: não tem rota pública (spec 019).
Autenticação Bearer JWT. Frontend usa BFF `/jalapao-store/api/` com cookies HttpOnly.
`products/` GET/POST/PATCH, `movements/` GET/POST, `sales/` GET/POST,
`product-images/` GET/POST/DELETE e `product-images/{uuid}/content/` GET autenticado,
`listing-drafts/` GET/POST/PATCH para preparar anúncios por canal,
`sales/{uuid}/` GET/PATCH/DELETE, `sales/{uuid}/receive/` e `cancel/` POST,
`cash/` GET/POST, `dashboard/` GET. PATCH corrige os campos financeiros permitidos com
`expected_updated_at` e `request_key`; DELETE faz exclusão lógica com estornos.
`receipts/` GET/POST, `receipts/{uuid}/` GET e `receipts/{uuid}/pay/` POST (occurred_on).
`receipts/{uuid}/cancel` POST (spec 023) desfaz uma entrada lançada errada sem apagá-la; exige
change_receipt, add_movement e add_cashentry, e só vale se ela for a última movimentação do
produto. Compra já paga gera um CashEntry de entrada ligado por `refund_of_receipt`.
Criar entrada exige add_receipt e add_movement; pagar exige add_receipt, change_receipt e
add_cashentry. Produção não gera caixa. Compra paga cria CashEntry com vínculo único.
Movimento de ajuste positivo exige unit_cost; negativo usa a média. Campos stock_value e
average_cost são somente leitura no produto. SaleItem.cost_total é o custo exato da baixa;
unit_cost é arredondado para apresentação e pode não reproduzir o total multiplicado.
Paginação padrão 100; pesquisar produto com `?search=`, filtrar category/active, vendas channel/status.
Respostas inválidas: `{"errors":{"campo":["mensagem"]}}`. HTTP 400 validação, 401 login,
403 permissão, 404 recurso. Valores monetários em strings decimais.

JWT: access 15 minutos, refresh 1 dia, rotação e blacklist. O logout invalida refresh;
access já emitido pode durar até 15 minutos. Expurgar blacklist expirada com
`uv run python manage.py flushexpiredtokens` em manutenção periódica.
GET exige view_model, POST add_model, PATCH change_model. Venda também exige add_movement;
receber/cancelar exige change_sale, add_movement e add_cashentry. Admins têm acesso total.

## Operações
`import_legacy /legacy/produtos.json`: uma transação, identifica legacy_id, não sobrescreve.
`bootstrap_users`: lê BOOTSTRAP_PASSWORD do ambiente, cria admin/jpmorais superusers somente
se ausentes, não redefine senhas. Django armazena hash. Nunca commitar arquivo de bootstrap.
Interface Django Admin em `/jalapao-store/admin/`; estoque/caixa/vendas são apenas leitura
no Admin para não contornar os serviços. Usuários e grupos continuam administráveis.

Todas as specs ficam em ../docs/specs (uma pasta por mudança); as regras gerais estão em
../docs/specs/001-platform e ../docs/specs/002-stock-cost.

Contrato OpenAPI versionado: docs/openapi.yml. Validar com
`uv run python manage.py spectacular --validate --fail-on-warn --file docs/openapi.yml`.
Documentação interativa só na cópia local, em `http://localhost:8080/api/v1/docs/`, depois de
entrar no Django Admin (`http://localhost:8080/jalapao-store/admin/`) ou com autenticação JWT. A sessão Django é aceita somente nas telas de documentação;
as operações comerciais da API continuam usando JWT.
