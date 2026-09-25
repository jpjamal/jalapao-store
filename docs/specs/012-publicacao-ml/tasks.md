# Tarefas

- [x] Cliente: subir foto em multipart, criar anúncio devolvendo item ou causas, gravar descrição.
- [x] Ajuste de `family_name`/`title` compartilhado entre validação e criação.
- [x] `publicar`: trava, sem estoque recusa, valida de novo, fotos, criação, descrição, `Listing`.
- [x] `Listing.draft`, permissão `publish_listingdraft` e migrações.
- [x] Endpoint `POST listing-drafts/{id}/publish` e `published_item_id` no rascunho.
- [x] Tela: botão depois de validar, confirmação, resultado com link e situação na lista.
- [x] Testes sem rede (11 novos).
- [x] Publicar pelo GitHub (acb1af3, 24/09/2026), com as correções da primeira publicação real
      (5ba89ac, 40c2c66, ebaf5fe).
- [x] Permissão de publicar: o usuário da loja já publicou sem ajuste.
- [x] Primeira publicação real: Dummy Aranha, MLB7700023302, em 25/09/2026.
- [x] Rascunho publicado continua sendo o editor do anúncio: **Salvar e enviar ao Mercado
      Livre** (`push`) manda preço, fotos novas, atributos e descrição; alteração pendente
      visível na tela e na lista. Substituiu o botão avulso de reenviar descrição, que chegou a
      ser feito e não foi publicado.
- [ ] Primeiro envio real ao MLB7700023302 — deve gravar a descrição que faltou.
