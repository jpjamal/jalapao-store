# 004 — Busca de produto por digitação

## Comportamento
- Onde se escolhe um produto, o campo deixa de ser uma lista suspensa e passa a ser busca:
  digita-se parte do nome ou do código e a lista filtra enquanto se escreve. São três
  lugares: o produto de **cada item** da venda, o produto da entrada de compra/produção e
  o produto do ajuste de inventário.
- A busca ignora acento e caixa: `luminaria` encontra `Luminária Air FOrm`. Casa por
  trecho em qualquer posição do nome ou do SKU, não só pelo começo.
- Teclado: ↓ e ↑ percorrem, Enter escolhe o item destacado, Esc fecha e devolve o campo ao
  que estava escolhido. Clicar fora também devolve.
- Cada linha mostra o saldo do produto, como a lista suspensa já mostrava.
- Escolher um produto continua disparando o que disparava antes: preço sugerido na venda,
  custo sugerido na entrada.
- No máximo 50 itens desenhados por vez, com aviso de quantos ficaram de fora.

## Meia escolha não passa
Digitar um nome e sair sem selecionar nada **apaga o texto**. Sem texto, o campo obrigatório
barra o envio no próprio navegador. É deliberado: o alternativo seria um formulário que
parece preenchido e chega ao servidor sem produto, e o erro apareceria tarde, em forma de
validação da API.

## Limites e não objetivos
- Quem filtra é o navegador, sobre a lista já carregada — não há busca no servidor. Para o
  tamanho deste catálogo é de sobra; se um dia passar de alguns milhares de itens, o lugar
  de resolver é o endpoint, que já aceita `search`.
- Não cria produto a partir do que foi digitado, nem sugere o mais vendido primeiro: a
  ordem é a do catálogo.
- Vendas e compras seguem listando **apenas produtos ativos**; o ajuste de inventário
  alcança também os desativados, exatamente como antes da mudança.

## Aceitação
Digitar `luminaria` na venda encontra `Luminaria Air FOrm` e, ao escolher, preenche o preço
unitário. Digitar `shen` na entrada, descer com ↓ e confirmar com Enter seleciona
`suporte shenlong` e traz o custo sugerido. No estoque, escolher pela busca e registrar um
movimento grava no produto certo e limpa o formulário. Digitar um nome e sair sem escolher
impede o envio.
