# 025 — Lucro real na tela inicial

## Objetivo

A tela inicial mostrava um único lucro, o **estimado**, que soma o lucro de **todas as vendas
confirmadas**, inclusive as que ainda estão a receber. O dono quer ver também o **lucro real**, o que
já virou dinheiro, a partir das vendas.

## Regras

- **Lucro previsto** (antes "lucro estimado"): soma do lucro de todas as vendas **confirmadas**, recebidas
  ou não. É o mesmo número de antes, só com o nome do dono.
- **Lucro real**: soma do lucro das vendas **confirmadas que já foram recebidas** (`received_at`
  preenchido). O lucro de cada venda continua sendo o de sempre: líquido (bruto − desconto − taxas reais −
  frete pago pela loja) menos o custo dos itens congelado na venda.
- Venda **cancelada** não entra em nenhum dos dois, mesmo que tenha sido recebida antes de cancelar.
- Lucro real nunca passa do previsto; a diferença é o lucro das vendas ainda a receber.
- O lucro real **não desconta** despesas lançadas à mão no Caixa, compras de insumo ou de estoque: o
  fluxo de caixa manual não altera o lucro das vendas (regra existente). Ele mede o resultado das vendas
  já recebidas, e não o saldo do Caixa.

## Não objetivos

Lucro por período, lucro por canal, descontar despesas e insumos (isso seria um resultado do negócio, e
não das vendas) e mudar o cálculo do lucro de cada venda.

## Validação

Testar sem vendas (ambos zero), venda recebida e venda a receber, taxa real da plataforma, e venda
recebida e depois cancelada.
