# Validação

Em 01/10/2026:

- Suíte completa (314 testes, 21 deles novos em `apps/common/tests/test_listagens.py`) contra PostgreSQL 17 real
  e também no SQLite: OK. Os 293 testes que já existiam continuam passando. `ruff`, `makemigrations --check`,
  contrato OpenAPI validado com `--fail-on-warn` e `tsc --noEmit`: OK.
- Backend: texto ordena sem ligar para acento e maiúscula nos dois bancos; números ordenam como número; nulos
  ficam no fim; insumo sem linha de saldo conta como zero; desempate estável entre páginas; coluna fora da lista
  é ignorada; busca por cada campo previsto e sem acento; período inclusivo nos dois lados; filtros de escolha
  inválidos dão 400 e os de sim ou não com valor sem sentido são ignorados; busca, filtro e ordem combinados.
- Telas conferidas no navegador, com dados de teste: Produtos (ordem por preço e por nome, seletor **Ordenar por**
  e `aria-sort` no cabeçalho), Estoque (posição e movimentações), Caixa (movimentos e categorias), Vendas,
  Insumos (lista, compras, movimentos e categorias), Entradas, Categorias, Anúncios (rascunhos) e Integrações
  (lojas e anúncios): busca, filtros, período, ordenar e limpar, sem erro no console.
- `next build`: OK.
