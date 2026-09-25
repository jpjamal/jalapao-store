# Plano

## Fontes consultadas
Documentação oficial do Mercado Livre, lida em 25/09/2026: *Buscador de produtos*
(`/products/search` com `q` ou `product_identifier`, `status`, `site_id`), *Mais vendidos*
(`/highlights/MLB/category/{id}`, 20 itens com `id`, `position`, `type`), *Busca de itens*
(`/items/bulk?ids=` substitui `/items?ids=`; a busca de itens de outros vendedores foi
descontinuada), *Referências de preços* e *Competição* (avaliadas e deixadas de fora: só valem
para os próprios anúncios).

## Onde cada coisa fica

| Onde | O quê |
|---|---|
| `integrations/meli/cliente.py` | `search_catalog`, `product`, `product_items`, `best_sellers`, `items`, `user_product` — só GET |
| `integrations/meli/pesquisa.py` | `preco_de` (formatos tolerados), `resumo` (menor, mediana, maior), `produtos`, `ofertas`, `mais_vendidos` |
| `integrations/api.py` | `GET integrations/price-products`, `price-offers`, `price-best-sellers` |
| `pesquisa-precos/page.tsx` | tela com as duas pesquisas |
| `components/ml-anuncio.tsx` | árvore de categorias exportada, com `onAbrir` para qualquer nível |

## Decisões
**Ações no ViewSet de integrações.** São consultas com a conta conectada; a permissão de ver
integrações já diz quem pode consultar o marketplace.

**Códigos validados antes de montar o caminho.** `product_id` e `category_id` aceitam só letras,
números e hífen; `gtin` só números.
