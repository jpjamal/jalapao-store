# Plano

`Receipt` ganha `status` (confirmada ou cancelada) e `cancelled_at`, como a venda. `CashEntry`
ganha `refund_of_receipt`, uma ligação própria para o estorno: `receipt` já é o pagamento e é
única, então o estorno não cabe nela.

`cancel_receipt` (em `inventory/services.py`) trava a entrada e o produto, confere que nenhuma
movimentação do produto é igual ou posterior à da entrada e chama `adjust_stock` com o novo
parâmetro `restore_value`. Ele faz a saída retirar exatamente o valor que a entrada pôs, no lugar
do custo médio, e recusa deixar o estoque com quantidade zero e valor diferente de zero. Sem esse
parâmetro nada muda nas demais saídas.

A regra "última movimentação" é o que garante a restauração exata: com outras movimentações no
meio, retirar o valor da entrada poderia deixar o custo médio incoerente. O cancelamento cria a
própria movimentação, então não se cancela duas vezes em sequência e a repetição devolve o
registro como está.

Migrações: `inventory 0004` (status e data) e `finance 0003` (estorno). Frontend: botão Cancelar
com confirmação, situação "Cancelada" e linha esmaecida; a rota `cancel` entra na lista do BFF.
