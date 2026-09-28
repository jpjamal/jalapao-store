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
| backend/ | Django: um app por contexto (domain, models, services, api, tests), settings por ambiente, uv.lock, Dockerfile |
| frontend/ | Next.js: rotas em app/, telas por contexto em features/, comum em shared/, PWA, Dockerfile |
| docs/ | Constituição SDD, decisões, specs, validação e operação |
| infra/ | script de publicação e o Traefik da cópia local; proxy e certificados de produção ficam no repositório `traefikproxy` |
| site/, api/, Dockerfile e nginx-site.conf da raiz | Sistema anterior (site estático + API de produtos) preservado para consulta/rollback; nenhum workflow, compose ou deploy os usa |
| manuais/ | PDFs públicos da loja, fora do rsync de código; o deploy os leva ao bucket do SILO (spec 020) |

Produção: https://jpsys.duckdns.org/jalapao-store (também pelo IP, https://217.216.82.25/jalapao-store)
Admin Django: https://jpsys.duckdns.org/jalapao-store/admin/
Retorno OAuth dos marketplaces: https://jpsys.duckdns.org/jalapao-store/callback

Um único proxy na VPS: o Traefik central (repositório `traefikproxy`, com o Portainer), que
termina o HTTPS e roteia pelos labels do compose da loja. Só o front e o Django Admin têm rota
pública; a API é consumida pelo front na rede interna. Fotos dos produtos e manuais em PDF
ficam no SILO, o servidor de arquivos da mesma stack. Ver [operação](docs/operations.md).

## Desenvolvimento orientado por especificação
Comece por [constituição](docs/constitution.md), [especificação](docs/specs/001-platform/spec.md),
[plano](docs/specs/001-platform/plan.md) e [tarefas](docs/specs/001-platform/tasks.md).
Cada mudança futura deve declarar comportamento, aceitação, plano e evidência de validação.
Índice de todas as specs, com o que ainda está pendente: [docs/specs](docs/specs/README.md).
Documentação própria: [backend](backend/README.md) e [frontend](frontend/README.md).
[Operação e recuperação](docs/operations.md). [Decisão monorepo](docs/adr/001-monorepo-modular.md).
[Arquitetura, organização do código e relações do banco](docs/architecture.md).

Guias: [manutenção (onde mexer)](docs/manutencao.md) · [produtos](docs/produtos.md) ·
[integrações](docs/integracoes.md) · ferramentas: [taxas de marketplace](docs/calculadora-marketplace.md),
[custo de impressão 3D](docs/custo-impressao-3d.md), [etiquetas](docs/gerador-de-etiquetas.md).
Versões antigas guardadas: [originais/LEIA-ME.md](originais/LEIA-ME.md).

## Escopo
Preço/custo decimal, histórico de estoque, venda por canal, descontos/taxas/frete reais,
lucro por venda, recebimento, estorno e lançamentos manuais. Cadastros antigos importados
por ID sem sobrescrita e com quantidade inicial zero. Calc. marketplace preserva estimativas
antigas: não substituir taxas reais das vendas por esses valores.

Marketplaces (Shopee e Mercado Livre): conectar a loja por autorização, espelhar anúncios
vinculando por SKU e enviar o saldo do estoque, com interruptor por anúncio e desligado por
padrão. O envio é sempre daqui para lá — saldo do marketplace nunca sobrescreve o local.
No Mercado Livre também: validar, publicar e editar anúncio a partir do rascunho (specs
011–012), pesquisa de mercado (013) e importar vendas com taxa e frete reais sob comando do
dono (015). Fora do escopo por enquanto: empurrar preço, campanha e Ads, e pedidos da Shopee.
Não há worker automático: a sincronia é a pedido.
A conta Mercado Livre foi conectada no domínio anterior. O token existente pode ser
renovado sem novo callback; uma nova autorização no domínio `jpsys.duckdns.org` ainda
depende de conferir o retorno cadastrado no DevCenter. Importação e envio remoto de
estoque ainda aguardam testes controlados. Ver [integrações](docs/integracoes.md).

Deploy de código exclusivamente via main → GitHub Actions. Segredos nunca no Git.
