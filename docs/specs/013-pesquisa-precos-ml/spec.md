# 013 — Pesquisa de preços no Mercado Livre

Tela **Pesquisa de preços**, em Marketplaces, para saber por quanto um produto está sendo
vendido no Mercado Livre e o que mais vende numa categoria. **Só consulta**: nada é gravado,
nada é enviado, nenhum anúncio muda.

## Comportamento

**Por produto.** O dono digita palavras (ex.: "carregador turbo 20W") ou o código de barras.
Só números, de 8 a 14 dígitos, é tratado como código de barras. A tela lista até 10 produtos do
catálogo do Mercado Livre com foto, marca, modelo, o preço de quem está ganhando a página do
produto e se o frete é grátis. **Ver todas as ofertas** mostra, para o produto escolhido, o
menor preço, a mediana, o maior e a quantidade de ofertas, e a lista da mais barata para a mais
cara, com condição, envio (Full, frete grátis) e tipo de anúncio.

**Mais vendidos da categoria.** O dono navega pela árvore de categorias (a mesma de Anúncios) e
pode consultar qualquer nível, não só a categoria final. A tela mostra os 20 mais vendidos, na
ordem, com nome, foto, preço e link, e a faixa de preços dos que vieram com preço.

## Decisões e limites

- **A busca aberta por texto em todos os anúncios não existe mais** na API. A pesquisa usa o que
  a documentação oferece: catálogo (`/products/search`, `/products/{id}`, `/products/{id}/items`)
  e mais vendidos (`/highlights`).
- **Catálogo cobre produtos de marca.** Peças autorais, como as impressas em 3D, costumam não
  estar no catálogo; para elas, a tela orienta a usar os mais vendidos da categoria.
- **Mais vendidos vêm só com ids.** Nome e preço saem de uma segunda consulta, conforme o tipo:
  anúncio (`/items/bulk`, uma chamada para todos), produto do catálogo (`/products/{id}`) ou
  produto do vendedor (`/user-products/{id}`). Produto do vendedor pode vir sem preço; aparece
  com "—".
- **Formato ainda não visto com a conta real.** A leitura de preço procura nos campos conhecidos
  (`price`, `price.amount`, `sale_price.amount`, `buy_box_winner.price`). Quando não acha,
  registra uma amostra da resposta no log, para ajustar ao formato verdadeiro.
- **Permissão:** a mesma de ver integrações (`integrations.view_marketplaceaccount`).
- `/items?ids=` está sendo descontinuado até 25/10/2026; a pesquisa já usa `/items/bulk`.
