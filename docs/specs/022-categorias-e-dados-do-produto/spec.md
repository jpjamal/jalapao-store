# 022 — Categorias no lugar do tipo; marca, modelo e peso

## Objetivo

O produto deixa de ter "tipo" (revenda ou impressão 3D) e passa a ter **categoria**, uma lista
que o dono cadastra. O produto também ganha **marca**, **modelo** e **peso** (gramas), todos
opcionais. As categorias iniciais são **Eletrônicos** e **Produção Impressão 3D**.

## Regras

- `Category`: nome (único, sem diferenciar maiúscula, minúscula ou acento nas letras), ativa ou
  inativa e a opção `uses_printing_profile`. Sem apagar; desativar tira da lista de escolha, e
  os produtos que já estão nela continuam e podem ser editados.
- `uses_printing_profile` substitui o tipo: produto de categoria com a opção ligada **exige** os
  parâmetros de impressão 3D (custo e preço calculados por eles); nas outras, custo e preço
  são digitados e os parâmetros 3D são recusados. A opção **não muda** depois que a categoria
  tem produtos, para não deixar produto sem parâmetros.
- Todo produto tem categoria. Na API, se ela não vier: parâmetros 3D levam à categoria de
  produção 3D; caso contrário, à primeira categoria comum ativa (a mais antiga). Assim código
  e importações antigos continuam válidos.
- Categoria inativa não recebe produto novo nem troca de categoria, mas quem já está nela
  pode ser salvo sem mudar.
- Mover um produto para categoria comum apaga o perfil 3D dele; movê-lo para uma de produção
  3D exige os parâmetros na mesma edição.
- Migração: produto de impressão 3D vira "Produção Impressão 3D"; os demais viram
  "Eletrônicos". O campo `kind` deixa de existir.
- Marca e modelo são texto de até 100 caracteres. Peso é decimal em gramas, não negativo,
  vazio quando desconhecido. Não substitui o peso do filamento dos parâmetros 3D.
- A busca de produtos também encontra por marca e modelo, e a lista filtra por categoria.
- Fora desta spec: enviar marca, modelo, peso ou categoria a marketplace (o rascunho de anúncio
  já tem os próprios campos de marca e modelo), unidade de peso diferente de grama e
  hierarquia de categorias.

## Validação

Testar criação e listagem de categorias com contagem de produtos, nome repetido (inclusive com
acento e maiúscula), trava da opção 3D, ausência de DELETE, categoria padrão, produto 3D sem
categoria, parâmetros exigidos e recusados conforme a categoria, troca de categoria, categoria
inativa, marca/modelo/peso e a busca por eles, filtro por categoria, migração dos produtos
existentes de tipo para categoria e ausência de migrações pendentes.
