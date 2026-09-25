# 013 — Pesquisa de mercado no Mercado Livre

Tela **Pesquisa de mercado**, em Marketplaces (endereço `/pesquisa-precos`), para ver o que
mais vende em cada categoria do Mercado Livre e quais produtos existem no catálogo. **Só
consulta**: nada é gravado, nada é enviado, nenhum anúncio muda.

Nasceu como pesquisa de preços. A primeira consulta real mostrou que a API não entrega o preço
dos concorrentes para esses produtos (ver validação), e o dono escolheu manter a tela como
ranking e descoberta, com link para conferir o preço no site.

## Comportamento

**Mais vendidos da categoria** (aba inicial). O dono navega pela árvore de categorias (a mesma
de Anúncios) e pode consultar qualquer nível, não só a categoria final. A tela mostra os 20 mais
vendidos, na ordem, com nome, marca, modelo e foto, e o link **Ver preços no Mercado Livre**.

**Buscar produto.** O dono digita palavras (ex.: "carregador turbo 20W") ou o código de barras.
Só números, de 8 a 14 dígitos, é tratado como código de barras. A tela lista até 10 produtos do
catálogo com nome, marca, modelo, foto e o mesmo link.

**O link.** Quando o Mercado Livre devolve o endereço da página (`permalink`), é ele. Quando vem
vazio — o caso dos produtos de catálogo vistos até aqui —, é a busca do site pelo nome da
família do produto, que sempre abre e mostra os anúncios com preço.

## Decisões e limites

- **Sem preço de concorrente.** Os produtos vieram como página tradicional
  (`pdp_types: traditional`), sem vendedor ganhando a página (`buy_box_winner: None`), e
  `/products/{id}/items` respondeu 404 "No winners found". A consulta de ofertas foi retirada.
  Ler o site direto (raspagem) foi descartado: vai contra os termos de uso e quebra fácil.
- **A busca aberta por texto em todos os anúncios não existe mais** na API.
- **Catálogo cobre produtos de marca.** Peças autorais, como as impressas em 3D, costumam não
  estar no catálogo; para elas vale o ranking da categoria.
- **Mais vendidos vêm só com ids.** Nome, marca e foto saem de uma segunda consulta, conforme o
  tipo: anúncio (`/items/bulk`, uma chamada para todos), produto do catálogo (`/products/{id}`)
  ou produto do vendedor (`/user-products/{id}`).
- **Permissão:** a mesma de ver integrações (`integrations.view_marketplaceaccount`).
- Referência de preço dos próprios anúncios (`/suggestions/items/{id}/details`) é a consulta
  oficial que devolve preço concorrente; ficou de fora por decisão do dono, e pode entrar depois.
