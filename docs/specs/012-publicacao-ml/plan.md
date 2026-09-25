# Plano

## Fontes consultadas
Documentação oficial do Mercado Livre, lida em 24/09/2026: *Publicar produtos* (`POST /items`;
no modelo User Products o título "não deverá ser enviado"; descrição em chamada própria depois
de criar), *Imagens* (`POST /pictures/items/upload` em multipart devolve o `id` da foto para
usar em `pictures`; JPG/PNG, até 10 MB), *User Products* (`family_name`, `user_product_id`,
`family_id`) e *Descrição de produtos* (`plain_text`).

## Onde cada coisa fica

| Onde | O quê |
|---|---|
| `integrations/meli/cliente.py` | `upload_picture` (multipart), `create_item` (400 vira causas), `set_description`; transporte aceita `raw` |
| `integrations/meli/anuncio.py` | `ajustar_envio`, o ajuste de `family_name`/`title`, agora usado pela validação e pela criação |
| `integrations/meli/publicacao.py` | `publicar` e `enviar_alteracoes`, sobre as mesmas peças: trava, fotos (só as novas), descrição conferida, vínculo |
| `integrations/meli/cliente.py` (envio) | `update_item` (`PUT /items/{id}`), `get_description`, `set_description` com substituição |
| `integrations/models.py` | `Listing.draft` (um para um com o rascunho, `SET_NULL`), `pushed_at`, `picture_ids` |
| `catalog/models.py` | permissão `publish_listingdraft` |
| `catalog/drafts_api.py` | `POST {id}/publish`, `POST {id}/push`; `published_item_id` e `pending_changes` no rascunho |
| `anuncios/page.tsx` | botão, confirmação, resultado e situação na lista |

O vínculo fica no `Listing` (que já dependia do catálogo) e não no rascunho, para não criar
dependência do catálogo para as integrações.

## Decisões
**O 400 da criação é resposta.** Como na validação, `create_item` não passa pelo `_request`
comum: o corpo do 400 traz as causas que explicam a recusa.

**Tudo dentro de uma transação.** As chamadas ao Mercado Livre acontecem com o rascunho
travado. É mais lento que o ideal, mas a publicação é rara e manual, e a trava é o que impede
dois cliques de criarem dois anúncios.
