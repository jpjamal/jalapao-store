# 034 — Visualizar o item da listagem

Pedido do dono: as listagens só tinham ícones de ação, sem tela para ver o item. Cada linha passa a abrir
uma janela flutuante de visualização, com os dados completos e os mesmos botões da linha.

## Comportamento

- Clicar em qualquer ponto da linha (ou no texto principal dela, que é um botão e funciona pelo teclado)
  abre a janela. Clicar num ícone, link, campo ou caixa de seleção da linha continua fazendo só a ação dele.
- A janela mostra os dados do item em pares rótulo/valor, mais o que for específico (produtos da venda,
  insumos usados, descrição) e, no rodapé, os botões de ação **com ícone e texto**.
- Usar um botão da janela fecha a visualização antes de abrir a edição ou a confirmação que ele pede, para
  não empilhar janelas. Esc, o botão Fechar e o clique fora também fecham.
- Vale para: Vendas, Produtos, Categorias, Entradas (compras e produção), Insumos, compras e movimentos de
  insumos, categorias do Caixa e de insumos, rascunhos de Anúncios e, em Integrações, contas, anúncios
  vinculados e anúncios sem produto.
- Itens sem ação (movimentos de insumo, vínculos) mostram só os dados.

## Compatibilidade

Só apresentação: sem mudança de API, banco, cálculo, estoque ou Caixa. As ações são as mesmas funções da
linha, chamadas pela janela.

## Aceitação

Clicar na linha abre a janela com os dados certos; os botões da janela funcionam como os da linha; clicar
nos ícones da linha não abre a janela; teclado (Tab até o texto da linha, Enter) e Esc funcionam.
