# Manutenção

Como o projeto é montado e onde mexer. Para publicar, escalar e recuperar, veja
[operação](operations.md); para o desenho do banco, [arquitetura](architecture.md).

> Reescrito em 23/09/2026. Antes disso este documento descrevia um site estático sem
> build, sem framework e sem banco. Esse sistema virou `site/` e `api/` — ficam no
> repositório para consulta e rollback, e não são mais servidos.

## Estrutura

Organizada por contexto desde a spec 017 — o mapa completo, as regras de dependência e onde
cada arquivo antigo foi parar estão em [arquitetura](architecture.md).

```
jalapao-store/
├── backend/            Django 5.2 + DRF, PostgreSQL, uv
│   ├── apps/<contexto>/  accounts, catalog, inventory, sales, finance, integrations, common
│   │   ├── domain/       regras puras, sem banco
│   │   ├── models.py     entidades
│   │   ├── services.py   casos de uso transacionais
│   │   ├── api/          serializers, permissions, views, urls
│   │   └── tests/        os testes do contexto
│   ├── apps/integrations/  + domain/ports.py, infrastructure/ (clientes ML e Shopee),
│   │                         services/ (sincronização e casos de uso do Mercado Livre)
│   └── config/settings/  base, production (padrão), development, test
├── frontend/           Next.js 16 (App Router), React 19, Tailwind 4, shadcn/ui
│   └── src/
│       ├── app/          só rotas (cada page.tsx reexporta a tela) e o BFF em app/api/
│       ├── features/     telas e componentes por contexto; tools/lib/ tem as contas das ferramentas
│       └── shared/       cliente da API, ui/, componentes comuns, layout (menu), format, PWA
├── infra/              nginx (http/https/dev), deploy.sh e renovação de certificado
├── docs/               constituição, arquitetura, specs, operação e por ferramenta
├── site/, api/         o sistema anterior, preservado para rollback
└── manuais/            PDFs públicos, fora do repositório no servidor
```

## Onde mora cada responsabilidade

A regra que vale para todo contexto do backend:

| Camada | Onde | O que pode ter |
|---|---|---|
| domínio | `domain/` | conta e regra puras, sem ORM e sem request |
| caso de uso | `services.py` | transação, trava, validação de regra |
| borda | `api/` | serialização, permissão, rota, formato da resposta |

Serviço só roda dentro de `transaction.atomic`, e toda escrita de estoque passa por
`adjust_stock` — é lá que moram a trava de concorrência e o razão de movimentos.

No frontend a ideia é a mesma: as contas das ferramentas vivem em
`src/features/tools/lib/` e não tocam em DOM. As telas leem campo, chamam a função e desenham.

## As ferramentas

As três são páginas do app desde 23/09/2026, em `/ferramentas/*`. As contas foram
portadas linha a linha dos arquivos antigos, **sem alterar nenhuma fórmula**:

| Módulo | Veio de | Cuidado |
|---|---|---|
| `features/tools/lib/custo3d.ts` | `site/assets/custo-3d.js` | precisa dar o mesmo número que `apps/catalog/domain/pricing.py` |
| `features/tools/lib/marketplace.ts` | o miolo de `site/calculadora.html` | as faixas de taxa são regra de negócio do dono |
| `features/tools/lib/etiquetas.ts` | o miolo de `site/etiquetas.html` | os recortes do OCR são calibrados; mexer quebra a leitura |

O Tesseract continua vindo de CDN, carregado sob demanda na primeira leitura. A etiqueta é
desenhada pela API pública do Labelary, limitada a 3 requisições por segundo — daí a fila
com 360 ms de espaçamento e o retry no HTTP 429.

## Design system

Os tokens saem de `Jalapao Midia/Paleta_Jalapao_design_system.html` e estão em
`frontend/src/app/globals.css`, como variáveis em `:root` e no bloco de tema escuro.
São o **único** lugar para mexer em cor — nada de hex solto em componente.

| Token | Uso |
|---|---|
| `--background` `--card` `--muted` | fundos |
| `--foreground` `--muted-foreground` | texto |
| `--border` `--input` | filetes e campos |
| `--primary` `#a54d0b` | botões e links |
| `--cerrado` `#c8670f` | dominante, **só em bloco** — nunca texto pequeno |
| `--destructive` `--success` | valores negativos e positivos |

Tipografia: Bahnschrift nos títulos e rótulos, serifada no corpo, Consolas em número
(classe `.money`). O tema escuro acompanha o sistema operacional; cor nova entra nos dois
blocos. Texto branco sobre o laranja cerrado só passa em tamanho grande — para texto
pequeno sobre bloco colorido, use o laranja queimado.

## Acrescentar uma tela

1. Escreva a spec antes: `docs/specs/<numero>-<nome>/spec.md`, depois plan, tasks e
   validation. É o que a [constituição](constitution.md) exige, e vale também para mudança
   pequena.
2. Backend, no app do contexto: regra pura em `domain/` → modelo → migration → caso de uso em
   `services.py` → `api/serializers.py`, `api/views.py` e a rota em `api/urls.py`. Contexto
   novo entra na lista `CONTEXTOS` de `config/urls.py`.
3. Frontend: tela em `src/features/<contexto>/<nome>-page.tsx`, rota em `src/app/(store)/<rota>/page.tsx`
   com uma linha (`export { default } from "@/features/...";`) e link em `src/shared/layout/shell.tsx`.
4. Testes em `backend/apps/<contexto>/tests/`; regra pura com `SimpleTestCase`, sem banco.
5. Atualize o README da pasta e o documento da ferramenta em `docs/`.

## Testar antes de dar por pronto

Tudo junto, como em produção:

```bash
docker compose up --build
```

e abra <http://localhost:8080/jalapao-store>.

Backend isolado, exatamente o que o CI roda:

```bash
cd backend
uv sync --frozen
uv run ruff check . --exclude migrations
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/openapi.yml
DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py test apps --noinput
```

Sem PostgreSQL à mão, `TEST_SQLITE=1` roda a suíte em SQLite — mas os quatro testes de
concorrência se marcam como pulados, e são justamente os que já esconderam um problema.
**Antes de publicar, rode ao menos uma vez contra PostgreSQL de verdade.**

Frontend: `npm ci && npm run build` (o build valida TypeScript).

A cada mudança, confira: login, as telas do menu, tema claro e escuro, largura de celular
(375 px basta) e, nas ferramentas, um caso com resposta conhecida — os pedidos reais
documentados em [calculadora de marketplace](calculadora-marketplace.md) e
[custo de impressão 3D](custo-impressao-3d.md).

## Armadilhas já pagas

- **Thread de teste precisa fechar a própria conexão.** `close_old_connections()` não fecha
  conexão recente enquanto o `CONN_MAX_AGE` de 60s a considera viva; as threads morriam com
  a conexão aberta e o `destroy_test_db` falhava com *"database is being accessed by other
  users"*. Os 22 testes passavam e o job voltava com exit 1 mesmo assim — e o deploy nunca
  rodava. Use `connection.close()` no `finally`.
- **O Traefik não roteia container fora de `healthy`.** Ele some da tabela sem erro no log;
  o sintoma é 404 com `"-"` na coluna de router do access log.
- **`localhost` em healthcheck de Alpine** resolve `::1` primeiro. Use `127.0.0.1`.
- **Arquivo em bind mount troca de inode no rsync.** Por isso o `deploy.sh` recria
  `gateway` e `tls` com `--force-recreate` depois de publicar.
- **Regra de negócio não muda sozinha.** As taxas de marketplace só mudam com pedido
  explícito e, de preferência, conferidas contra um pedido real do painel.

## O canvas de design

As telas do sistema anterior existem como desenho editável em
<https://claude.ai/artifact/1ThGkYiqa72SKVSkZL69Ln>, com fontes em `design/*.dc.html` e
`canvas.json`. É desenho, não é o site: mudar lá não muda as telas — e ele ainda retrata o
site antigo.
