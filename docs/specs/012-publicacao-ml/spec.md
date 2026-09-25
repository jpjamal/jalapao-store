# 012 — Publicar o rascunho no Mercado Livre

Entrega 3 da [spec 009](../009-rascunhos-anuncios/spec.md). Depois da validação da
[spec 011](../011-validacao-anuncio-ml/spec.md), o rascunho ganha a ação que **cria o anúncio
de verdade** e liga o rascunho ao anúncio criado.

## Comportamento

**Quando aparece.** O botão **Publicar no Mercado Livre** só aparece depois de uma validação
que terminou em "Pronto para publicar", e só em rascunho que ainda não foi publicado.

**Confirmação.** Publicar pede uma segunda confirmação na tela, dizendo o que vai: quantas
fotos, o preço e que a quantidade disponível é o estoque atual do produto. Tirar do ar depois
é pelo painel do Mercado Livre.

**O que acontece, em ordem:**
1. Recusa sem chamar o Mercado Livre se o rascunho já foi publicado ou se o produto está sem
   estoque. A simulação aceitava 1 unidade de mentira; a publicação não — seria vender o que
   não existe.
2. Valida de novo, igual à spec 011 (local e simulado). Se não puder publicar, para aqui.
3. Sobe as fotos do rascunho, na ordem escolhida, para o Mercado Livre
   (`POST /pictures/items/upload`, multipart). As fotos da loja são privadas, então não há URL
   pública para o campo `source`.
4. Cria o anúncio (`POST /items`) com os ids das fotos e o estoque real. No modelo "produto do
   vendedor", manda `family_name` e, se o Mercado Livre recusar, tira `title` — o mesmo ajuste
   da validação.
5. Grava a descrição (`POST /items/{id}/description`, texto simples).
6. Cria o `Listing` ligado ao produto e ao rascunho, com `item_id`, `user_product_id` e
   `family_id` devolvidos.

**Depois de publicado, o rascunho continua sendo onde o anúncio é editado.** A tela mostra
"Publicado como MLB…" e se há alterações no rascunho ainda não enviadas. O botão de validar dá
lugar a **Salvar e enviar ao Mercado Livre**, que manda ao anúncio (`PUT /items/{id}`):
- preço;
- fotos, na ordem do rascunho — só as que ainda não estão lá sobem;
- atributos;
- descrição, criada ou substituída (`PUT …/description?api_version=2`) só quando mudou, e
  conferida depois por `GET`;
- título, só em anúncio do modelo clássico — no "produto do vendedor" quem monta é o Mercado
  Livre.

Categoria e estoque não vão: categoria não muda depois de publicado, e o estoque segue a
sincronização de Integrações. Antes de enviar, roda a checagem local da spec 011 (fotos,
atributos obrigatórios, limites da categoria); com erro, o anúncio não é tocado.

A lista de rascunhos mostra "Publicado · MLB…" e, se for o caso, "alterações não enviadas".

## Decisões e limites

- **Nunca publica duas vezes.** O rascunho é travado (`select_for_update`) durante a
  publicação e a existência do `Listing` ligado a ele é conferida antes de qualquer chamada.
- **Permissão própria.** Publicar exige `catalog.publish_listingdraft`, além de alterar
  rascunho. Validar continua só com alterar.
- **Sincronização de estoque desligada.** O `Listing` nasce com `sync_enabled = false`; ligar
  continua sendo escolha do dono em Integrações, como nos anúncios importados.
- **Falha antes de criar não deixa anúncio.** Fotos que já subiram ficam soltas na conta do
  Mercado Livre, sem anúncio, e não aparecem para ninguém.
- **Falha na descrição não desfaz o anúncio.** O anúncio já existe; a falha vira aviso para
  completar pelo painel do Mercado Livre.
- **Frete não é enviado.** Vale o modo de envio configurado na conta (o aviso `User has not
  mode me1` da spec 011 vem disso). Tipo de anúncio fixo em Clássico (`gold_special`).
- **Custo interno nunca sai**, como na validação.
- **Alteração pendente** é o rascunho salvo depois do último envio (`Listing.pushed_at`).
- **Fotos não sobem de novo:** `Listing.picture_ids` guarda foto da loja → id no Mercado Livre.
- **Fora do escopo:** pausar ou encerrar pelo sistema, trocar categoria, variações, Premium,
  frete e Shopee.
