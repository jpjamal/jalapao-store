# 023 — Cancelar compra ou produção lançada errada

## Objetivo

Uma compra ou produção registrada com produto, quantidade ou custo errado precisa poder ser
desfeita. O sistema não apaga histórico (constituição, regra 3): o registro **é cancelado** e
continua na lista como "Cancelada", como já acontece com a venda.

A venda já tinha essa opção (`cancel_sale`: devolve os itens ao estoque e estorna o
recebimento). Esta spec dá o equivalente às entradas de estoque.

## Regras

- `POST /receipts/{id}/cancel/`, com permissão de alterar entrada, movimentar estoque e lançar
  no caixa. O botão **Cancelar** fica na lista de Compras e produção.
- Só cancela enquanto a entrada for a **última movimentação do produto** (nenhuma venda, ajuste,
  cancelamento ou outra entrada depois dela). Assim tirar as unidades e o valor dela devolve o
  estoque **exatamente** ao que era, sem distorcer o custo médio de outras entradas. Fora disso
  a API recusa com explicação e nada muda; a correção passa pelos ajustes de estoque.
- O estoque perde a quantidade e o valor **da própria entrada** (não o custo médio do momento).
- Compra já paga: entra no caixa um estorno de entrada com o mesmo valor, ligado à compra.
  Compra não paga e produção não mexem no caixa.
- A entrada fica com `status = cancelled` e `cancelled_at`; a movimentação original permanece e
  uma nova movimentação de saída registra o cancelamento.
- Cancelar duas vezes não repete nada. Compra cancelada não pode ser paga.

## Não objetivos

Editar quantidade ou custo de uma entrada (cancela e lança de novo), cancelar quando já houve
outras movimentações (use o ajuste), apagar registros e mudar o cancelamento de venda.

## Validação

Testar a restauração exata do estoque com entradas antigas de outro custo, compra sem
pagamento, compra paga com estorno único, produção, recusa após venda, ajuste ou nova entrada,
cancelamento da mais recente, pagamento de compra cancelada e a API (sucesso, recusa e permissão).
