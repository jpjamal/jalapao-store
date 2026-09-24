# 010 — SKU automático do produto

## Objetivo

Todo produto novo cadastrado recebe um código estável sem digitação manual. O código começa
com `SKU`, seguido das iniciais do nome sem acentos e de um número global crescente com no
mínimo quatro dígitos: `Luminária Pimentão` → `SKU-LP-0001`. Palavras de ligação comuns
não entram nas iniciais. Nomes sem letras ou números utilizam `PRD`.

## Regras

- O número identifica a ordem de reserva de novos códigos; **não** representa o saldo.
- A quantidade fica em `Stock.quantity` e muda por entradas, vendas ou ajustes, sem trocar SKU.
- A geração ocorre no backend para API, Django Admin e ferramenta 3D; o frontend só mostra o resultado.
- A API ignora SKU enviado em criação/edição. Importações legadas com SKU explícito preservam o código.
- SKUs existentes não são migrados, pois podem ser usados nos vínculos de marketplace.
- Uma tabela com chave auto incremental reserva números sem depender de contagem de produtos.
  Se um SKU manual legado ocupar um código candidato, a geração avança para o próximo número.

## Validação

Testar criação sequencial de nomes iguais, quantidade separada, edição sem troca de SKU,
importação com SKU explícito e ausência de migrações pendentes.
