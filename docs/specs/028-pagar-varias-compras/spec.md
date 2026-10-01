# 028 — Pagar compras: janela de confirmação e pagamento em lote

## Objetivo

Hoje, "Pagar" numa compra abre um formulário no topo da página, longe do botão, e só paga uma compra por vez.
O dono pediu (1) uma **janela flutuante** só para confirmar e (2) **caixas de seleção** para pagar várias
compras de uma vez. Vale para as duas listas de compras: **Compras e produção** (produtos) e **Insumos**
(aba de compras).

## Como funciona

- **Pagar uma compra:** o botão "Pagar R$ …" da linha abre uma janela no meio da tela, com o resumo (quantidade ×
  nome, valor) e os botões **Confirmar pagamento** e **Cancelar**. Esc e clique fora também cancelam. Não há
  campo de data: o pagamento sai com a data de hoje.
- **Pagar várias:** cada compra **a pagar** (confirmada, de produto ou insumo, ainda sem pagamento) ganha uma caixa
  de seleção. O cabeçalho tem uma caixa que marca ou desmarca todas as a pagar **da lista que está na tela**.
  Compra paga, cancelada ou produção própria não tem caixa.
- Com alguma marcada, aparece uma faixa acima da lista: "N compras selecionadas · total R$ X", com
  **Pagar selecionadas** e **Limpar seleção**. O botão abre a mesma janela, agora com a lista das compras e o
  total, e **Confirmar pagamento** paga todas.
- A seleção vale só para o que está visível: mudar a busca, o filtro, a ordem ou a página tira da seleção o que
  saiu da tela, para nunca pagar uma compra que o dono não está vendo.
- Cada compra gera a sua própria saída no Caixa, como hoje, uma única vez: pagar de novo uma compra já paga (por
  exemplo, paga em outra aba enquanto a janela estava aberta) é aceito sem lançar outra saída.
- **Se uma falhar** no meio do lote, o pagamento para ali: as já pagas continuam pagas, a janela continua aberta
  só com as que faltam e diz qual deu erro (quantidade, nome e valor) e por quê, para tentar de novo.
- Depois de pagar, a tela rola até o aviso ("Pagas N compras…").

## Regras

- Nenhuma mudança na API, nos dados ou nas regras de pagamento: o lote chama o pagamento de cada compra, na
  ordem em que aparecem na tela.
- O motivo de não haver "tudo ou nada": cada pagamento é uma saída de dinheiro independente, e as pagas ficam
  corretas mesmo se outra falhar.

## Não objetivos

Escolher a data do pagamento, pagar compras de páginas diferentes ao mesmo tempo, lote para cancelar.

## Validação

Conferir na tela, nas duas listas: pagar uma pela janela (confirmar e cancelar, Esc), marcar várias e pagar, a
caixa do cabeçalho, a seleção que some ao mudar o filtro, compra paga ou cancelada sem caixa, e uma falha no meio
do lote (a janela fica com as que faltam). O auxiliar `payInOrder` (paga em ordem e para no primeiro erro) é conferido por um erro forçado no meio do lote,
porque o frontend ainda não tem rodador de testes.
