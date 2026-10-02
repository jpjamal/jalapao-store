# 029 — Custo sugerido no ajuste de estoque e produtos sem estoque destacados

## Objetivo

Dois pedidos do dono em 02/10/2026:

1. Ao dar entrada de estoque de uma peça 3D, o custo por unidade já vir preenchido com o custo de produção do
   cadastro, sem precisar abrir o produto para ver quanto ele custa.
2. Produtos **sem estoque** marcados com outra cor nas listas, para achar de olho.

## Como funciona

- **Estoque → Ajustar inventário:** com quantidade positiva, o campo "Custo unitário da entrada" já vem com o
  custo do cadastro do produto escolhido — na peça 3D, o custo de produção calculado pelos parâmetros 3D (o mesmo
  "custo de referência" da lista de produtos). Uma linha embaixo diz de onde veio o valor ("Custo de produção 3D do
  cadastro: R$ …"). O campo continua editável: vale o custo real daquele lote. Trocar de produto troca a sugestão.
- **Compras e produção** já fazia isso (origem "Produção própria / 3D" ou compra): nada muda lá.
- **Sem estoque** (saldo zero ou menor): nas listas de **Produtos** e **Estoque → Posição atual**, a linha ganha
  fundo avermelhado e o selo "Sem estoque" ao lado da quantidade; no celular, o cartão da linha também. No seletor
  de produto (vendas, entradas, estoque), o lugar da quantidade mostra "sem estoque" em vermelho.
- A cor sai do token `--destructive` da paleta, então acompanha o tema claro e o escuro.

## Regras

- Nenhuma mudança na API nem nos dados: o custo sugerido é o `cost_price` que o produto já tem.
- O custo médio do estoque continua vindo do custo informado em cada entrada; a sugestão só preenche o campo.

## Não objetivos

Recalcular o custo do cadastro quando o preço do filamento muda (o cadastro guarda o custo do momento em que foi
salvo; a spec 024 avisa com `price_outdated`). Alerta de pouco estoque (estoque baixo, não zerado).
