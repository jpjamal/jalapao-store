# Plano

## Fontes consultadas
Documentação oficial do Mercado Livre, lida em 25/09/2026: *Orders*
(`/orders/search?seller=&order.status=&order.date_created.from=&sort=date_desc`, `/orders/{id}`;
`order_items[].sale_fee`, `payments[].marketplace_fee`, `shipping.id`, estados `paid` e
`cancelled`). O custo do envio para o vendedor (`/shipments/{id}/costs`, campo `senders`) não
estava explícito na página de custos de envio; por isso a leitura é tolerante e avisa.

## Onde cada coisa fica

| Onde | O quê |
|---|---|
| `sales/models.py` | canal `site`; `Sale.external_id` com unicidade por canal (migração 0004) |
| `integrations/meli/cliente.py` | `orders_search`, `order`, `shipment_costs` — só GET |
| `integrations/meli/pedidos.py` | `taxa_do_pedido`, `frete_do_vendedor`, `ler_pedido`, `previa`, `importar` |
| `sales/api.py` | `GET sales/ml-preview?days=`, `POST sales/ml-import` |
| `components/importar-vendas-ml.tsx` | painel de prévia e importação, usado em Vendas |
| `config/settings.py` | `SaleChannelEnum` aponta para `Sale.Channel` (sem lista copiada) |

## Decisões
**Reuso da regra de venda.** A importação chama `create_sale` e `cancel_sale`, as mesmas da venda
manual: estoque, custo médio, líquido e estorno ficam num lugar só.

**Transação por pedido.** Um pedido que falha (sem estoque, por exemplo) não impede os outros.

**Contrato OpenAPI** (`backend/docs/openapi.yml`) regenerado: estava parado desde a entrega de
fotos e rascunhos e não tinha as rotas das specs 011 a 015.
