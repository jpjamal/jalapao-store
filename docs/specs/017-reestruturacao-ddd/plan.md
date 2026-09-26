# Plano

## Referências
Padrões seguidos: Django (layout por app, settings por ambiente, camada de serviço, DRF com
serializers/views/urls separados), Python (imports absolutos e ordenados, type hints nas
regras novas, dataclass para valor calculado), backend (camada de serviço, porta/adaptador
para o marketplace, erros tratados num lugar) e frontend (feature folders, composição,
componentes pequenos com um papel).

## Execução — mecânica e verificável
Mover centenas de imports à mão arrisca deixar um para trás. A mudança foi feita por scripts,
com `git mv` (histórico preservado), e conferida a cada fase:

1. **Mover e reescrever imports** (backend): imports relativos viram absolutos nos caminhos
   antigos; `git mv` de cada arquivo; um mapa caminho antigo → novo reescreve imports, alvos
   de `patch` dos testes, strings de settings e os dois imports das migrações.
2. **Separar a API** por papel com a árvore sintática do Python (`ast`): classes de serializer,
   de permissão e o resto; `ruff` remove imports que sobraram e acusa nome faltando.
3. **Rotas por contexto** e comparação do contrato OpenAPI gerado com o commitado.
4. **Extrair o domínio** e cobrir com testes puros (`SimpleTestCase`, sem banco).
5. **Settings por ambiente** e CI apontando para `config.settings.test`.
6. **Frontend**: `git mv` para `features/` e `shared/`, rotas reexportando a tela, imports por
   alias reescritos pelo mapa, `lib/api.ts` dividido por nome importado; `tsc` e `next build`.
7. **Subir a cópia local** com as imagens novas e testar rotas.

Cada fase termina com ruff, `check`, `makemigrations --check`, contrato validado e os testes.
