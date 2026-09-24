# Backend Jalapão Store

Django 5.2 LTS, DRF, SimpleJWT, PostgreSQL 17, Python 3.13 na imagem.
Gerenciador: **uv**; dependências exatas em `uv.lock`. Nunca instalar no Python global.

## Desenvolvimento
Na pasta backend, `uv sync --frozen` cria `.venv`. Configurar DJANGO_SECRET_KEY,
POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_DB=jalapao e POSTGRES_USER=jalapao no ambiente.
Executar `uv run python manage.py migrate` e `uv run python manage.py runserver`.
Banco isolado com backend/compose.yml (`docker compose --env-file ../.env up --build`).
Stack completa: compose da raiz. `.env.example` contém apenas valores de desenvolvimento.

`TEST_SQLITE=1` permite testes rápidos locais; não usar em produção. Concorrência é
testada somente em PostgreSQL no CI. Rodar `uv run python manage.py test apps.common`.
Rodar `uv run ruff check . --exclude migrations` e `uv run python manage.py makemigrations --check`.

## Organização e contratos
- accounts: usuário Django extensível, grupos/permissões, JWT e bootstrap explícito.
- catalog: Product e PrintingProfile 1:1; cálculos em domain.py.
- inventory: saldo 1:1, histórico N:1, serviços atômicos com bloqueio do produto.
- inventory.Receipt: compras/produções por produto com custo congelado; Stock.value mantém
  avaliação pelo custo médio móvel. Product.cost_price é apenas referência de novas entradas.
- sales: Sale 1:N SaleItem; snapshots, chave idempotente e cancelamento reversível.
- finance: entradas/saídas imutáveis. Recebimento e estorno por venda são únicos.
- integrations: Listing relaciona produto interno a item/user_product/family; outbox transacional.
  Tokens de marketplace são cifrados em repouso com chave derivada de DJANGO_SECRET_KEY;
  preserve esse segredo ao atualizar a instalação. Cada anúncio Shopee acompanha a versão
  de estoque enviada, para não encerrar eventos de outras contas nem reenviar saldo antigo.

App por domínio; ORM é persistência, services são casos de uso, api é camada HTTP.
Históricos usam PROTECT. Sem DELETE comercial. Desativar produtos pelo campo active.

API interna `/api/v1/`; pública via `/jalapao-store/backend-api/`.
Autenticação Bearer JWT. Frontend usa BFF `/jalapao-store/api/` com cookies HttpOnly.
`products/` GET/POST/PATCH, `movements/` GET/POST, `sales/` GET/POST,
`sales/{uuid}/receive/` e `cancel/` POST, `cash/` GET/POST, `dashboard/` GET.
`receipts/` GET/POST, `receipts/{uuid}/` GET e `receipts/{uuid}/pay/` POST (occurred_on).
Criar entrada exige add_receipt e add_movement; pagar exige add_receipt, change_receipt e
add_cashentry. Produção não gera caixa. Compra paga cria CashEntry com vínculo único.
Movimento de ajuste positivo exige unit_cost; negativo usa a média. Campos stock_value e
average_cost são somente leitura no produto. SaleItem.cost_total é o custo exato da baixa;
unit_cost é arredondado para apresentação e pode não reproduzir o total multiplicado.
Paginação padrão 100; pesquisar produto com `?search=`, filtrar kind/active, vendas channel/status.
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

Specs específicas em docs/specs; especificação compartilhada em ../docs/specs/001-platform.

Contrato OpenAPI versionado: docs/openapi.yml. Validar com
`uv run python manage.py spectacular --validate --fail-on-warn --file docs/openapi.yml`.
Documentação interativa em `/jalapao-store/backend-api/docs/` após entrar no Django Admin
ou com autenticação JWT. A sessão Django é aceita somente nas telas de documentação;
as operações comerciais da API continuam usando JWT.
