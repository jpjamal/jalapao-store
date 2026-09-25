# Tarefas

- [x] Métodos do cliente: sugestão de categoria, categoria, atributos e `items/validate`.
- [x] Regras puras de checagem local e tradução das causas do Mercado Livre.
- [x] Endpoints de consulta e de validação, com permissões e contrato OpenAPI.
- [x] Tela: sugestão de categoria, formulário de atributos, contador do título e relatório.
- [x] Testes sem rede, incluindo que nenhuma chamada de criação acontece.
- [x] Publicar pelo GitHub (commit 35b179f, 24/09/2026).
- [x] Categoria escolhida navegando a árvore do Mercado Livre (`GET /sites/MLB/categories` e
      `children_categories` de `GET /categories/{id}`), no lugar de digitar o código. Só categoria
      final (sem filhas) é aceita; a sugestão pelo título posiciona a árvore. Endpoint
      `listing-drafts/ml-category-tree`.
- [x] Fora do Mercado Livre, mesma entrega: motivos prontos no ajuste de estoque (Compra /
      reposição, Produção 3D, Contagem de inventário, Perda / defeito, Devolução), com texto
      livre ainda aceito. O motivo segue obrigatório (INV-01).
- [x] Primeira simulação real (Dummy Aranha, 24/09/2026) devolveu `body.required_fields
      [family_name]`: a conta está no modelo "produto do vendedor". A simulação agora reenvia com
      `family_name` (= título) e, se o Mercado Livre recusar `title`, sem ele. Máximo de duas
      novas tentativas, só consulta.
- [x] Validar o rascunho real do Dummy Aranha contra o Mercado Livre, com a conta conectada
      (24/09/2026, depois do 74c8708): "Pronto para publicar", sem erros. Dois avisos, nenhum
      bloqueia: GTIN condicional (peça artesanal, sem código) e `User has not mode me1` — a
      conta não usa o Mercado Envios 1; como o envio não é mandado, o Mercado Livre aplica o
      modo de frete da conta. Tratar frete na entrega de publicação.
