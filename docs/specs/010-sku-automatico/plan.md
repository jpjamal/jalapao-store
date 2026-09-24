# Plano

`SkuSequence`, uma tabela com chave auto incremental, reserva o número: cada produto novo
cria uma linha e usa a chave dela. Contar produtos não serve — apagar um produto faria o
número repetir, e duas criações simultâneas contariam o mesmo total. A sequência do banco
resolve os dois casos sem trava explícita.

A montagem do código (`SKU-` + iniciais sem acento, sem palavras de ligação + número com
quatro dígitos) acontece no `save()` do `Product` quando o SKU vem vazio. Por estar no
modelo, vale para API, Django Admin e ferramenta de impressão 3D sem repetir lógica.

A API trata `sku` como somente leitura: ignora o que vier na criação e na edição. A
importação legada escreve direto no modelo com o SKU antigo e por isso o preserva — os
vínculos de marketplace casam por SKU e não podem perder a referência.

Se um SKU manual antigo já ocupar o código gerado, reserva o número seguinte.

Os testes não assumem que a sequência reinicia entre casos: no PostgreSQL ela não volta
atrás quando a transação do teste é desfeita, e o CI roda em PostgreSQL.
