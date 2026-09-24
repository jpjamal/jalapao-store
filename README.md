# Jalapão Store

Gestão da loja: produtos de revenda e impressão 3D, estoque, vendas e caixa.
Monorepo **Django + DRF / Next.js**, PostgreSQL, autenticação JWT, Tailwind e shadcn/ui.

## Iniciar
1. Copiar `.env.example` para `.env` (somente desenvolvimento).
2. `docker compose up --build`.
3. Criar usuário: `docker compose exec backend python manage.py createsuperuser`.
4. Abrir http://localhost:8080/jalapao-store.

Backend sem Docker: `uv sync --frozen` dentro de backend cria o ambiente `.venv` isolado.
Frontend: `npm ci` dentro de frontend. Consulte os READMEs de cada pasta para configuração.

## Organização
| Pasta | Finalidade |
|---|---|
| backend/ | Django, apps por domínio, migrations, uv.lock, testes, Dockerfile e compose com DB |
| frontend/ | Next.js, componentes, as três ferramentas, package-lock e Dockerfile |
| docs/ | Constituição SDD, decisões, specs, validação e operação |
| infra/ | Proxy, HTTPS e publicação |
| site/, api/ | Fontes legadas preservadas para consulta/rollback; fora da nova stack |
| manuais/ | PDFs públicos da loja, fora do rsync de código |

Produção: https://217.216.82.25/jalapao-store
Admin Django: https://217.216.82.25/jalapao-store/admin/
Callback reservado: https://217.216.82.25/jalapao-store/callback

## Desenvolvimento orientado por especificação
Comece por [constituição](docs/constitution.md), [especificação](docs/specs/001-platform/spec.md),
[plano](docs/specs/001-platform/plan.md) e [tarefas](docs/specs/001-platform/tasks.md).
Cada mudança futura deve declarar comportamento, aceitação, plano e evidência de validação.
Documentação própria: [backend](backend/README.md) e [frontend](frontend/README.md).
[Operação e recuperação](docs/operations.md). [Decisão monorepo](docs/adr/001-monorepo-modular.md).
[Arquitetura e relações do banco](docs/architecture.md).

## Escopo
Preço/custo decimal, histórico de estoque, venda por canal, descontos/taxas/frete reais,
lucro por venda, recebimento, estorno e lançamentos manuais. Cadastros antigos importados
por ID sem sobrescrita e com quantidade inicial zero. Calc. marketplace preserva estimativas
antigas: não substituir taxas reais das vendas por esses valores.

Marketplaces (Shopee e Mercado Livre): conectar a loja por autorização, espelhar anúncios
vinculando por SKU e enviar o saldo do estoque, com interruptor por anúncio e desligado por
padrão. O envio é sempre daqui para lá — saldo do marketplace nunca sobrescreve o local.
Fora do escopo por enquanto: publicar ou editar anúncio, importar pedido e taxa real,
empurrar preço, campanha e Ads. Não há worker automático: a sincronia é a pedido.
Nenhuma conexão real foi exercitada ainda; ver [integrações](docs/integracoes.md).

Deploy de código exclusivamente via main → GitHub Actions. Segredos nunca no Git.
