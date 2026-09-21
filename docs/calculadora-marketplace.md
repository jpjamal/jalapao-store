# Calculadora de marketplace

`calculadora.html` — quanto sobra no bolso depois que o marketplace tira a parte dele.

## O que você preenche

| Campo | Observação |
|---|---|
| Shopee / Mercado Livre | troca a conta inteira; cada um tem suas taxas |
| Recarga automática de Ads (%) | só na Shopee. **Começa em 0 toda vez que a página abre**, de propósito |
| Vendedor CPF · pedidos em 90 dias | só na Shopee. Acima de 450 pedidos entram R$ 3,00 por item; abaixo é isento |
| Tipo de anúncio | só no Mercado Livre: clássico ou premium |
| Custo unitário do produto | o que a peça te custou, sem frete de entrada |
| Preço de venda desejado | o preço cheio anunciado |

A comissão **não** é escolha sua: ela sai da faixa de preço automaticamente.

## A conta da Shopee

```
faixa       = definida pelo preço de venda
taxas       = preço × comissão da faixa + taxa fixa da faixa + taxa de CPF
recarga     = preço × percentual de recarga
renda       = preço − taxas − recarga        ← o que a Shopee deposita
lucro       = renda − custo do produto
margem      = lucro ÷ preço
markup      = lucro ÷ custo
```

Tabela oficial, vendedor CNPJ:

| Faixa de preço | Comissão | Taxa fixa | Subsídio Pix |
|---|---|---|---|
| Abaixo de R$ 9,00 *(a partir de 01/10/2026)* | 20% | metade do preço | — |
| Até R$ 79,99 | 20% | **R$ 4,50** *(a partir de 01/10/2026)* | — |
| R$ 80 a R$ 99,99 | 14% | R$ 16,00 | 5% |
| R$ 100 a R$ 199,99 | 14% | R$ 20,00 | 5% |
| R$ 200 a R$ 499,99 | 14% | R$ 26,00 | 5% |
| Acima de R$ 500 | 14% | R$ 26,00 | até 8% |

**A calculadora já está usando os valores de 1º de outubro de 2026, antecipados** — decisão
do dono da loja, para não ter que lembrar de trocar nada na data. A taxa fixa da primeira
faixa sobe R$ 0,50 e, junto com ela, o teto do meio-preço vai de R$ 8 para R$ 9 (esse teto
é sempre o dobro da taxa fixa). O resto da tabela não muda.

**Consequência no período de transição:** até 30/09/2026 a Shopee ainda cobra R$ 4,00, então
em toda venda de até R$ 79,99 a calculadora mostra R$ 0,50 a menos de lucro do que você
realmente recebe. O erro é para o lado seguro, some sozinho em 1º de outubro, e está
avisado na tela junto da tabela.

Quatro coisas que a tabela esconde:

- **O programa de frete grátis é obrigatório** desde março de 2026 e os 6% dele já estão
  dentro dessa comissão. Por isso o extrato do pedido mostra duas linhas — "taxa de
  comissão líquida" e "taxa de serviço líquida" — que somadas dão o valor da tabela. Não
  existe mais escolher programa.
- **A taxa de transação já está dentro da comissão.** Não há nada a somar por fora por
  forma de pagamento.
- **O teto de R$ 100 por item acabou.** Produto caro paga os 14% cheios.
- **O vendedor CPF paga R$ 3,00 por item a mais** depois de 450 pedidos em 90 dias. Abaixo
  disso é isento — é o caso da loja hoje, confirmado pelo pedido real de R$ 79,99, que foi
  cobrado exatos R$ 20,00 sem o adicional. O seletor na tela liga essa taxa quando o volume
  crescer.

### O subsídio Pix não é taxa

A Shopee dá um desconto ao comprador que paga por Pix (5% nas faixas do meio, até 8% acima
de R$ 500) e **abate o mesmo valor da própria comissão**. No exemplo oficial de um item de
R$ 500: o comprador paga R$ 460, a comissão cai de R$ 96 para R$ 56, e o vendedor recebe
R$ 404 nos dois casos. Como o líquido não muda, o subsídio não entra na conta.

O que muda é o **valor na nota fiscal** — R$ 460 em vez de R$ 500 —, e é sobre ele que sai
imposto. Venda no Pix dá base de tributação menor com o mesmo dinheiro no bolso.

### Subsídio de frete

A Shopee cobre o frete até R$ 20 para itens de até R$ 79,99, até R$ 30 de R$ 80 a
R$ 199,99 e até R$ 40 acima de R$ 200. É o que zerou o frete nos dois pedidos conferidos —
por isso ele não entra na conta.

### Recarga automática de Ads

É um percentual do pedido que a Shopee retém e converte em saldo de anúncios. Aparece no
extrato como "Taxa da Recarga Automática (Pedido)". O mínimo de adesão é 2%, e o crédito
**não volta** se o pedido for cancelado.

Incide sobre o **preço cheio do produto**, não sobre o subtotal com cupom — confirmado em
dois pedidos: 3% de R$ 79,99 = R$ 2,40 e 5% de R$ 229,99 = R$ 11,50, ambos exatos.

O campo volta para 0 a cada abertura porque você liga e desliga conforme a campanha; um 3%
esquecido do mês passado distorceria todos os preços em silêncio.

## A conta do Mercado Livre

```
comissão = 13% (clássico) ou 17,5% (premium)
extra    = R$ 6,50 se o preço for menor que R$ 79,00
taxas    = preço × comissão + extra
```

**Atenção:** esses percentuais são médias de mercado para categorias gerais, não a tabela
oficial. A comissão do Mercado Livre muda por categoria — confira a sua no anúncio antes de
fechar preço. Essa parte da calculadora não foi verificada contra pedido real.

## Verificação contra pedidos reais

Dois pedidos do painel da Shopee, conferidos no centavo:

| Pedido | Taxas reais | Calculadora | Renda real | Calculadora |
|---|---|---|---|---|
| R$ 79,99 · recarga 3% | 20,00 | 20,50 | 57,59 | 57,09 |
| R$ 229,99 · recarga 5% | 46,70 | 58,20 | 160,29 | — |

O primeiro batia exato até a taxa fixa nova ser antecipada; a diferença de R$ 0,50 é
exatamente o ajuste de outubro e desaparece em 1º/10. O segundo é um pedido **anterior a março de 2026**: foi cobrado pela
estrutura antiga (20% = 14% + 6% do frete grátis, mais R$ 3,00 de taxa fixa), que dá
exatamente os R$ 46,70. Pela tabela de hoje, o mesmo preço pagaria R$ 58,20 — a calculadora
está certa para pedidos novos.

## O que a calculadora NÃO desconta

Se algum destes valer para você, tire na mão:

- **Cupom do vendedor.** A Shopee desconta o cupom antes de aplicar a comissão, e o valor
  também sai do seu bolso. A calculadora trabalha só com o preço cheio.
- **2,5% de campanha de destaque**, durante a promoção.
- **Até R$ 10,00 por devolução** com culpa do vendedor.
- **Frete.** Nos dois pedidos conferidos ele fechou em zero para o vendedor — o comprador e
  o subsídio da Shopee cobriram o parceiro logístico. Se no seu caso sobrar frete, ele não
  entra aqui.
- **Impostos.** Nada de Simples, MEI ou IR está nessa conta.

## Quando a Shopee mudar a tabela

Três lugares em `calculadora.html`:

1. `tabelaVigente(hoje)` — guarda a taxa fixa da primeira faixa e o teto do meio-preço, e a
   data em que os valores novos entram (`AJUSTE_OUTUBRO`). É aqui que se programa uma
   mudança anunciada com antecedência.
2. `faixaShopee(preco, hoje)` — as faixas em si; devolve comissão, taxa fixa e o nome da
   faixa. Aceita uma data para dar para testar o futuro sem mexer no relógio.
3. `atualizarTabela()` — o texto que aparece em "Ver tabela de regras e taxas".

Mudou uma, mude as outras, senão a tela passa a mentir.

## Fontes

- **Política de Comissão para vendedores CNPJ e CPF**, Centro de Educação do Vendedor da
  Shopee — artigo de 04/02/2026, última atualização em 18/09/2026. É a fonte oficial e
  prevalece sobre as demais; foi dela que vieram o ajuste de 01/10/2026, a taxa de CPF, o
  subsídio Pix e os subsídios de frete.
- [Ecommerce na Prática — taxa Shopee 2026](https://ecommercenapratica.com/blog/taxa-shopee/)
- [Irroba — novas taxas Shopee 2026](https://blog.irroba.com.br/novas-taxas-shopee-2026-guia-de-comissoes-e-frete/)
- [Shopee Ads — Recarga Automática (Pedido)](https://ads.shopee.com.br/learn/faq/340/2236)
- [Centro de Educação do Vendedor Shopee](https://seller.shopee.com.br/edu/article/26839/Comissao-para-vendedores-CNPJ-e-CPF-em-2026)

Pesquisa feita em 14/09/2026 e conferida contra o artigo oficial em 18/09/2026.
