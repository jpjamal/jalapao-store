# 015 — Vendas por canal e importação manual de vendas do Mercado Livre

A loja vende no Mercado Livre, na Shopee, pelo site Jalapão e direto (boca a boca). O que
interessa é o **estoque** e o **registro da venda para o caixa**. Toda venda, de qualquer canal,
segue a mesma regra: baixa o estoque pelo custo médio, desconta taxa, frete e desconto para
chegar ao líquido, e entra no caixa quando o dono marca como recebida.

## Comportamento

**Canais da venda:** Boca a boca, **Site Jalapão** (novo), Mercado Livre, Shopee e Outro.
A venda manual continua igual e serve para todos.

**Importar do Mercado Livre** (tela Vendas), sempre por comando do dono:
1. **Buscar vendas** do período escolhido (7 a 90 dias) mostra uma prévia, sem criar nada. Cada
   pedido aparece com itens, bruto, taxa, frete, líquido e a situação:
   - *Nova* — pronta para importar (vem marcada);
   - *Já importada* — não pode ser importada de novo;
   - *Pendente* — algo impede: anúncio sem produto vinculado em Integrações, produto inativo,
     mesmo produto em duas linhas com preços diferentes;
   - *Cancelada no Mercado Livre* — a venda importada antes será cancelada (vem marcada).
2. **Importar selecionados** cria as vendas (canal Mercado Livre, referência "Pedido ML …") e
   cancela as dos pedidos cancelados, devolvendo o estoque. O resultado diz o que entrou, o que
   foi cancelado e o que falhou, com o motivo.

**Valores:** bruto = preço × quantidade dos itens; taxa = `marketplace_fee` dos pagamentos (na
falta, `sale_fee` de cada item × quantidade); frete = o que coube ao vendedor no envio
(`senders` dos custos do envio). Se o frete não puder ser lido, a prévia avisa e a venda entra
com frete zero, para o dono conferir.

## Decisões e limites

- **Nada automático.** Sem aviso do Mercado Livre nem rotina periódica; o dono decide quando
  sincronizar. Evita configuração no painel do aplicativo enquanto não há volume de vendas.
- **Um pedido, uma venda.** A venda guarda o código do pedido (`external_id`, único por canal) e
  a chave de idempotência é derivada dele; importar de novo não duplica.
- **Números vêm do Mercado Livre, não da tela:** a importação busca cada pedido de novo.
- **Sem estoque, não importa:** a venda falha com o motivo e nada muda. Registre a entrada e
  importe de novo.
- **Recebimento continua manual:** a venda importada fica "a receber"; o caixa só muda quando o
  dono marca como recebida — o Mercado Livre libera o dinheiro dias depois.
- **Desconto de cupom não é lido** nesta versão (entra zero); cupom do vendedor, se houver, o dono
  ajusta.
- **Shopee fica para depois:** a conta ainda não está conectada; a venda da Shopee continua
  manual.
- Permissões: prévia exige mexer em estoque e ver integrações; importar exige também alterar
  venda e lançar caixa (cancelar venda importada estorna caixa se já recebida).
