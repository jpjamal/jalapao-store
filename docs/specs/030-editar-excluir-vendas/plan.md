# Plano

Serviços transacionais em sales com bloqueio da venda. SaleRevision guarda snapshots e a chave
da correção; Sale.deleted_at marca exclusão lógica após cancel_sale. PATCH usa updated_at como
controle de concorrência e UUID para repetição segura. Origem importada em external_channel,
preenchida por migração; unicidade do pedido passa a usar essa origem estável.

CashEntry liga um ajuste à revisão, com categoria automática própria. A unicidade do recebimento
e estorno permanece para lançamentos sem revisão; cada revisão tem no máximo um ajuste.
Frontend usa componentes da feature de vendas, formulário com foco e confirmação de exclusão.
Testes em banco isolado, sem modificar dados comerciais do desenvolvimento ou produção.
