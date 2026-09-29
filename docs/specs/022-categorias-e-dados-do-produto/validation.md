# Validação

Em 29/09/2026:

- Suíte completa (187 testes) contra PostgreSQL 17 real, sem nenhum teste pulado: OK. Em
  SQLite, 187 com 5 pulados (concorrência): OK. `ruff`, `manage.py check`, contrato OpenAPI
  validado com `--fail-on-warn`, ausência de migrações pendentes, `tsc --noEmit` e
  `next build`: OK.
- Migração dos dados: teste que cria produtos com o modelo antigo (revenda e impressão 3D) e
  aplica a `0007` confirma "Eletrônicos" e "Produção Impressão 3D". A migração também rodou
  sobre o banco local de desenvolvimento, e o produto que já existia foi para "Eletrônicos".
- O teste de migração do estoque (`CostMigrationTests`) foi ajustado para fixar também o app
  `catalog` no estado anterior; continua provando que estoque e snapshots de venda antigos
  são preservados.
- Testes da API: criação e contagem, nome repetido com acento e maiúscula, trava da opção 3D,
  ausência de DELETE, categoria padrão, produto 3D sem categoria, parâmetros exigidos e
  recusados por categoria, troca de categoria com remoção do perfil 3D, categoria inativa,
  marca, modelo e peso (com busca e peso negativo recusado) e filtro por categoria.
- Na tela, com o app local: `/categorias` lista as duas categorias com a contagem de produtos;
  nome repetido em outra caixa foi recusado; categoria nova criada; ao escolher "Produção
  Impressão 3D" o formulário mostra os parâmetros e o produto salvo saiu com custo e preço
  calculados, marca e modelo na lista; produto novo começa em "Eletrônicos".
- Os produtos e a categoria criados nesse teste foram removidos do banco local depois.

## Limites da evidência
As telas não foram conferidas em celular nem no tema escuro, e não houve teste com o login
de um usuário sem permissão de superusuário. O `iexact` do SQLite não ignora maiúscula
acentuada, por isso o nome único usa `casefold()` no Python; a restrição `Lower(name)` do
banco é só a segunda barreira.
