# 037 — Retirada de estoque para uso pessoal

Pedido do dono: às vezes o dono pega um produto para uso próprio. Não é venda, nem perda, nem defeito, e
precisa ficar registrado como tal na movimentação de estoque.

## Comportamento

- Em **Estoque → Ajustar inventário**, o motivo ganha a opção **Uso pessoal** (junto de Compra / reposição,
  Produção 3D, Contagem de inventário, Perda / defeito e Devolução).
- Escolhida, aparece um aviso: a retirada sai do estoque ao **custo médio**, sem venda, sem entrada no Caixa e
  sem contar como perda ou defeito. Se a quantidade for positiva, o aviso pede o sinal de menos (−), porque
  uso pessoal é saída.
- No histórico de movimentos o motivo aparece como "Uso pessoal", e dá para achá-lo pela busca.

## Compatibilidade

Só apresentação: o motivo já era um texto livre gravado no movimento. Sem mudança de API, banco, cálculo,
estoque ou Caixa (ajustes não movimentam o Caixa).

## Aceitação

Registrar uma saída de 1 unidade com o motivo "Uso pessoal": o saldo cai em 1, o valor em estoque cai pelo
custo médio e o movimento aparece no histórico com esse motivo.
