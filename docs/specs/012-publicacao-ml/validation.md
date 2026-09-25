# Validação

## Automática
119 testes passando (11 novos em `apps/common/test_publicacao_ml.py`), com o Mercado Livre
de mentira:
- ordem das chamadas: valida → sobe fotos → cria → descrição;
- fotos vão como ids na ordem do rascunho; estoque real, sem o mínimo de 1; custo não sai;
- segundo pedido de publicação não chama o Mercado Livre e não duplica o `Listing`;
- sem estoque e rascunho inválido param antes das fotos;
- recusa na criação não grava vínculo; pedido de `family_name` na criação é atendido;
- falha na descrição vira aviso e mantém o anúncio;
- endpoint exige `publish_listingdraft`; `published_item_id` aparece depois;
- cliente real com HTTP gravado: corpo multipart, 201/400 da criação, descrição em `plain_text`.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## Limites da evidência
Nada foi publicado de verdade até aqui. O que só a primeira publicação real confirma: o
formato exato da resposta do upload de foto, se a conta recusa `title` na criação, e o
`status` com que o anúncio nasce.
