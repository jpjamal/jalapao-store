# Plano

Regra pura em `apps/catalog/domain/gtin.py` (normalizar, dígito verificador, mensagem de
erro), sem banco e testável em `SimpleTestCase`, como o `sku.py`.

`Product.gtin` é `CharField(max_length=14, unique=True, null=True, blank=True)`. Vazio é
`NULL` e não texto vazio: o `unique` do PostgreSQL aceita vários `NULL`, mas recusaria dois
`""`. Por isso o `save()` do modelo normaliza sempre (`normalize_gtin(...) or None`), o que
cobre também Django Admin e importações. O mesmo validador roda no formulário do Admin.

Na API, o `ProductSerializer` declara o campo à mão (aceita vazio e `null`, limite folgado
para não cortar espaços antes de limpar) e valida em `validate_gtin`: limpa, confere a regra e
procura duplicidade excluindo o próprio produto. Não usa o validador de unicidade automático
porque ele compararia o texto antes da limpeza.

A busca do `ProductViewSet` ganha `gtin` em `search_fields`. No frontend, o campo de produto
com busca (`product-picker`) filtra também por GTIN no cliente, que é onde ele já filtra por
nome e SKU. A tela de Produtos ganha o campo e mostra o código junto do SKU na lista.

Migração `0006_gtin` só adiciona a coluna; produtos existentes ficam sem código.
