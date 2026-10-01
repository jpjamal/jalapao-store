# Plano

> Aprovada; ver a [spec](spec.md).

**Backend, uma peça comum.** `apps/common/filters.py` define os filtros que o DRF aplica a todas as listas
(`DEFAULT_FILTER_BACKENDS`): `FoldedSearchFilter` (busca sem diferenciar maiúscula nem acento) e
`StableOrderingFilter` (ordenação por lista fechada de colunas, com `pk` de desempate e nulos sempre no fim).
O "dobrar texto" é uma expressão de banco, `Fold`: no PostgreSQL `LOWER(TRANSLATE(...))` e no SQLite uma função
registrada, para a mesma regra valer na produção e nos testes rápidos. Uma expressão só, porque `Replace`
aninhado estoura o analisador do SQLite. Texto ordena pelo valor dobrado (o PostgreSQL de produção usa
colação byte a byte, que poria "Álcool" depois do "Z"); número ordena como número. Coluna que vem de uma
tabela ligada que pode não ter linha (saldo do insumo) conta como zero (`ordering_zero_fields`), para os dois
bancos darem a mesma ordem.

**Filtros por tela.** Cada app ganha um `api/filters.py` com um `FilterSet` (`range_filterset` monta os de
período `date_from`/`date_to`, inclusivos, e deixa acrescentar os filtros próprios: estoque com ou sem saldo,
recebimento, pagamento, origem do lançamento…). Cada view declara `search_fields`, `ordering_fields`,
`ordering_text_fields` e a ordem padrão que já tinha.

**Frontend, três peças comuns** em `shared/`: `lib/list.ts` (comparação de texto com acento, número e data),
`hooks/use-list-query.ts` (`useListQuery` para as listas do servidor, com espera de 0,3 s na busca e volta à
página 1; `useClientList` para as listas pequenas, que buscam, filtram e ordenam na tela) e os componentes
`SortableTh` (cabeçalho clicável: crescente, decrescente, padrão), `ListToolbar` (busca, filtros, período,
**Ordenar por** e **Limpar filtros**). O seletor **Ordenar por** existe porque o cabeçalho da tabela some no
celular. As 13 listagens passam a usar as mesmas peças.
