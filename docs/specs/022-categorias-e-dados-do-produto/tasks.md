# Tarefas

- [x] `Category` e `Product.category`, `brand`, `model`, `weight_g`; migração `0007` com os dados.
- [x] Remover `Product.kind`; regra 3D lida da categoria (API, Admin, importação legada).
- [x] API de categorias, filtro por categoria e busca por marca e modelo; contrato OpenAPI.
- [x] Frontend: tela de categorias, menu, BFF, formulário e lista de produtos.
- [x] Testes da API, dos padrões e da migração; teste de migração do estoque ajustado.
- [x] Documentação: specs, arquitetura, backend, frontend e guia de produtos.
- [x] Formulários de produto e categoria rolam até a tela ao abrir (correção do commit 68fd5ac: com a lista longa, o Editar de uma linha de baixo abria o formulário fora da área visível).
- [ ] Conferir as telas com login em celular e tema escuro.
- [x] Rodar a suíte contra PostgreSQL (187 testes, sem pulados).
- [ ] Publicação pelo GitHub (só quando o dono mandar).
