# Validação

## Backend
- 159 testes passando com `config.settings.test` (153 de antes + 6 novos de domínio puro), em
  5 s — antes 9 s, pelo hash de senha rápido dos testes.
- `ruff`, `manage.py check`, `makemigrations --check` (nenhuma migração nova) e contrato
  OpenAPI validado.
- **Contrato OpenAPI gerado depois da reestruturação idêntico ao commitado:** 41 rotas, 0
  linhas diferentes.
- Regras de dependência conferidas por busca: nenhum `domain/` importa ORM ou outro contexto;
  nenhum serviço fora de `integrations/infrastructure` importa cliente HTTP.

## Frontend
- `tsc` limpo; `next build` de produção gera as mesmas 18 rotas de antes.

## Cópia local (Docker, imagens novas)
- Backend com `config.settings.production` como padrão: `check --deploy` sem erro (o aviso de
  DEBUG é do compose de desenvolvimento, que liga DEBUG de propósito), 51 migrações aplicadas.
- Login, manifesto e health: 200; telas protegidas redirecionam ao login (307); API sem
  sessão: 401 — mesmo comportamento de antes.

## Limites da evidência
As telas por dentro não foram abertas na cópia local (exigem login). O fluxo autenticado está
coberto pelos testes do backend e pela compilação do frontend; a conferência visual fica para
produção depois do deploy.

## Publicação (26/09/2026)
- **Primeiro envio (934b595) falhou no build do frontend no CI**, sem chegar ao ar. A regra
  `lib/` do `.gitignore` da raiz (herdada de projetos Python) ignorava as pastas novas
  `frontend/src/shared/lib/` e `features/tools/lib/`: os arquivos existiam na máquina do
  desenvolvimento, por isso o build local passou, mas não foram para o commit.
- Corrigido em c5baabb: o `.gitignore` deixa de valer para `frontend/src/**/lib/`. Conferido que
  nenhum outro arquivo de código em `backend/apps`, `backend/config` e `frontend/src` estava
  ignorado. Pipeline completo verde e deploy feito.
- Produção depois do deploy: login e manifesto 200, telas protegidas 307 para o login, API sem
  sessão 401.
- Lição: conferir `git status --ignored` nas pastas de código depois de criar pastas novas.

