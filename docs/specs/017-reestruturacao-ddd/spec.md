# 017 — Reestruturação do código por contexto (inspirada em DDD)

O sistema cresceu entrega a entrega (specs 009–016) e o código ficou com pontos de acúmulo:
toda a API de um app num arquivo só (`drafts_api.py` com 400 linhas), 17 arquivos de teste
de todos os assuntos dentro de `apps/common`, regras de negócio misturadas com acesso ao
banco, o cliente HTTP do Mercado Livre na mesma pasta dos casos de uso, um `settings.py`
único e, no frontend, páginas de 300–500 linhas em `app/` e componentes de todos os assuntos
juntos em `components/`.

O dono pediu reestruturar backend e frontend seguindo os padrões de Django, Python, backend e
frontend, com estrutura inspirada em DDD e **sem mudar nenhuma funcionalidade nem tela**.

## Comportamento

Nenhum. Mesmas telas, mesmas rotas do frontend, mesmas 41 rotas da API com o mesmo contrato
OpenAPI byte a byte, mesmo banco (nenhuma migração nova; app labels e tabelas iguais).

## O que muda (só código)

- **Backend:** cada app Django é um contexto com `domain/` (regras puras), `models.py`,
  `services.py` (casos de uso), `api/` (`serializers`, `permissions`, `views`, `urls`) e
  `tests/`. `integrations` separa `domain/ports.py`, `infrastructure/` (clientes HTTP e cifra
  dos tokens) e `services/` (sincronização e casos de uso do Mercado Livre).
- **Regras extraídas para `domain/`:** arredondamento de dinheiro (núcleo compartilhado
  `common/domain/money.py`), custo médio de saída do estoque, totais da venda, iniciais do SKU.
- **Validade da autorização da Shopee** passa para o adaptador da Shopee: o serviço de
  sincronização deixa de conhecer detalhes de um marketplace específico.
- **Rotas:** cada contexto declara as suas em `api/urls.py`; `config/urls.py` só inclui.
- **Settings:** `config/settings/{base,production,development,test}.py`.
- **Testes:** cada contexto com os seus, em `apps/<contexto>/tests/`; o CI roda `test apps`
  com `config.settings.test`.
- **Frontend:** `app/` só com rotas; telas e componentes em `features/<contexto>/`; o que é
  de todos em `shared/`. `lib/api.ts` dividido em cliente, tipos comuns, formatação e tipos do
  catálogo; `ml-anuncio.tsx` (450 linhas) dividido por papel.

## Decisões

- **DDD pragmático, não literal.** Sem repositórios sobre o ORM nem entidades duplicadas: o
  Django já é a camada de persistência, e a constituição pede não inventar camadas. O que o
  DDD trouxe foi a separação por contexto e a regra de dependência (`api → services →
  domain/models`; `domain` sem ORM).
- **`services.py` continua um módulo por app** (padrão Django), e é a camada de aplicação.
  Só `integrations` virou pacote `services/`, porque tem vários casos de uso grandes.
- **App labels, tabelas e migrações intactos.** Duas migrações antigas tiveram só o caminho de
  import atualizado (`infrastructure.crypto`), sem mudar operação.
- **`production` é o padrão** do `manage.py` e do `wsgi`, igual ao antigo `settings.py`:
  deploy e containers não mudam de comportamento.
- **Specs antigas não foram reescritas**: registram os caminhos da época. A tabela "Onde
  procurar o que mudou de lugar", em docs/architecture.md, faz a ponte.
