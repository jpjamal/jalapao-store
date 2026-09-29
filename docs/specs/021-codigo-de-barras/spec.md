# 021 — Código de barras (GTIN) do produto

## Objetivo

O produto pode guardar o código de barras (GTIN/EAN) impresso na embalagem. O campo é
opcional e serve para uso futuro: leitor a laser na busca de produto e integração com
plataformas que pedem o GTIN do anúncio. Nesta spec o código só é **cadastrado, validado e
pesquisável**; nada envia o GTIN ao marketplace ainda.

## Regras

- Campo `gtin` no produto, **opcional**. Vazio vale como "sem código" (`null`); quantos
  produtos quiserem podem ficar sem.
- Aceita GTIN-8, GTIN-12 (UPC), GTIN-13 (EAN) e GTIN-14: só dígitos, com o tamanho certo e o
  **dígito verificador** conferido (pesos 3 e 1 da direita para a esquerda, GS1).
- Espaços e hífens digitados ou vindos do leitor são removidos; o que fica gravado é só o número.
- **Único**: dois produtos não podem ter o mesmo código. Corrigir o produto com o próprio
  código, sem mudá-lo, continua permitido.
- Não substitui o SKU: o SKU segue automático e é a chave dos vínculos de marketplace.
- A busca de produtos (API e campo de produto com busca das telas) também encontra pelo GTIN.
  O leitor a laser age como teclado (digita o número e dá Enter), então usa a mesma busca.
- A regra vale no backend (API, Django Admin e importações que passam pelo modelo); o
  frontend só mostra o campo e as mensagens de erro.

## Não objetivos

Enviar GTIN ao Mercado Livre ou à Shopee, ler código por câmera, gerar código de barras ou
etiqueta, e exigir GTIN para vender. Cada um vira spec própria se for preciso.

## Validação

Testar código válido de cada tamanho, dígito verificador errado, tamanho errado, letras,
limpeza de espaços e hífens, vários produtos sem código, duplicidade, edição com o próprio
código, apagar o código, busca pelo número e ausência de migrações pendentes.
