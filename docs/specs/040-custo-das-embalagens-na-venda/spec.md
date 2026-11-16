# 040 — Custo das embalagens no lucro da venda

Pedido do dono (16/11/2026): cadastrar as embalagens compradas (sacos plásticos, caixas de papelão e outras)
com custo unitário, controlar a quantidade em estoque e, na venda, escolher a embalagem usada. Decidido em
conversa: as embalagens ficam em **Insumos** (não no estoque de produtos) e o custo delas passa a sair do
**lucro de cada venda**, sem contar duas vezes no Resultado do negócio.

## Antes

- Embalagem já era insumo (categoria Embalagens), com compra, pagamento, baixa, ajuste e escolha na venda.
- O lucro da venda não descontava a embalagem. O custo entrava no **Resultado do negócio** só quando a compra
  era **paga** (Embalagens contava como despesa), de uma vez, mesmo com as caixas paradas no estoque.

## Agora

1. **Custo unitário do insumo** = o da última compra, ou o do último ajuste de entrada com custo. Muda só por
   esses caminhos (não se edita à mão). Cancelar a compra volta ao custo de antes, se ainda for o dela.
2. **Embalagens deixa de contar como despesa na compra.** Pagar a compra continua tirando do caixa, mas não
   desconta do resultado; o custo entra **venda a venda**, pelo que foi usado. Compras antigas mantêm a
   classificação congelada (spec 031).
3. **Na venda**, cada insumo usado tem o custo congelado na linha e o total (`supplies_cost`) sai do lucro:
   `lucro = líquido − custo dos produtos − custo dos insumos`. Como o Resultado do negócio soma o lucro das vendas
   recebidas, a embalagem entra nele pelo lucro.
4. **Saldo sem custo.** Parte do saldo sai **sem custo** nas vendas, para nada contar duas vezes:
   - todo o saldo que existia antes desta spec (já contado como despesa ou de custo desconhecido);
   - compras de categorias que **ainda contam como despesa** (ex.: Etiquetas e papelaria);
   - ajustes de entrada **sem** custo.
   Toda saída (venda, baixa, ajuste para menos) consome essa parte primeiro. Cancelar a venda devolve cada parte
   ao seu lugar.
5. **Filamento** escolhido numa venda sai sem custo: o custo dele já está na peça.
6. **Ajuste de entrada com custo** (opcional): para embalagens que já estavam em casa. Entra com o custo informado,
   que vira o custo do insumo, e não mexe no caixa.
7. **Embalagem padrão do produto**: lista de insumos por unidade vendida (ex.: Caneca = 1 Caixa M + 1 saco). Na
   venda, os insumos vêm preenchidos (kit × quantidade, somado por insumo) até a pessoa mexer neles; "Voltar para a
   embalagem padrão" refaz. Filamento não entra no kit.
8. A tela da venda mostra o **custo estimado** das embalagens antes de confirmar; o valor gravado é o do servidor.

## Fora do escopo

- Aviso de estoque baixo de embalagem (fica para depois).
- Vendas importadas do Mercado Livre continuam sem baixar insumo automaticamente.
- Custo médio ponderado: vale o último custo (como o preço do rolo do filamento).
- Recalcular vendas antigas: continuam com custo de insumo zero.

## Aceitação

- **040-C1** Compra de insumo cuja categoria não conta como despesa entra com custo; a que conta entra sem custo.
- **040-C2** Venda desconta do lucro o custo das unidades com custo; a parte sem custo sai primeiro e a zero.
- **040-C3** Cancelar a venda devolve o saldo e a parte sem custo; editar a venda mantém o custo dos insumos no lucro.
- **040-C4** Ajuste de entrada com custo entra com custo, atualiza o custo do insumo e não mexe no caixa; custo em
  ajuste de saída é recusado; custo unitário não se edita pelo cadastro.
- **040-C5** A migração deixa todo o saldo atual sem custo, preenche o custo com a última compra e desliga "conta como
  despesa" em Embalagens.
- **040-C6** Embalagem padrão por produto pela API (substitui a lista; vazia limpa; recusa filamento e repetido) e na
  tela; a venda vem preenchida e mostra o custo estimado; a janela da venda mostra o custo dos insumos.
