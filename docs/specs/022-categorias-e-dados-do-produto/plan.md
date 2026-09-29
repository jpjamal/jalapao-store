# Plano

`Category(Entity)` no app `catalog`, com nome único sem diferenciar maiúscula (restrição
`Lower(name)` no banco, mais a checagem com `casefold()` no serializer, porque o `iexact` do
SQLite não trata maiúscula acentuada). `Product.category` é chave estrangeira `PROTECT`
obrigatória no banco; o `save()` do modelo preenche a categoria padrão quando ela falta, no
mesmo estilo do SKU automático, o que mantém válidos os testes, o Admin e a importação legada.
`default_category()` e `printing_category()` escolhem a mais antiga ativa, comum ou de produção
3D, em vez de procurar pelo nome: renomear "Eletrônicos" não quebra o padrão.

O antigo `kind` sai. As regras que liam `kind == "printing"` (`ProductSerializer.validate`,
`update` e o Admin) passam a ler `category.uses_printing_profile`. A validação de parâmetros
3D vive em `validate`, e a mudança da opção com produtos dentro, em `CategorySerializer`.

Migração `0007`: cria `Category`, adiciona `category` (nula), `brand`, `model` e `weight_g`,
semeia as duas categorias e distribui os produtos pelo `kind`, torna `category` obrigatória e
remove `kind`. A operação de dados tem reversão (categoria volta para `kind`). Os nomes ficam
escritos na migração, que não depende do código do app.

API: `categories/` com listar, ver, criar e alterar (sem DELETE), `products_count` anotado,
filtros `active` e `uses_printing_profile`. `products/` filtra por `category` e busca também
por marca e modelo. Nome do campo do peso no formulário do frontend é `product_weight_g`,
porque `weight_g` já é o filamento nos parâmetros 3D e os dois entram no mesmo `FormData`.

Frontend: tela `features/catalog/categories-page.tsx` (rota `/categorias`, item no menu e
liberada no BFF), formulário de produto com categoria, marca, modelo e peso, e a lista com a
coluna de categoria. Produto novo começa na categoria comum mais antiga, a mesma que o
backend usaria. A ferramenta de custo 3D deixa de enviar `kind`; o backend a leva à categoria
de produção 3D.

O teste de migração do estoque (`CostMigrationTests`) passa a fixar também o app `catalog`
no estado anterior, senão o modelo histórico de produto ficaria em descompasso com o banco.
