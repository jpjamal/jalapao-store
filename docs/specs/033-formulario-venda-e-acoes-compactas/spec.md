# 033 — Formulário de venda e ações compactas

Pedido do dono: deixar o cadastro de venda na ordem natural do trabalho, permitir arrastar o arquivo ZPL
diretamente para a etiqueta e reduzir a poluição visual das listagens trocando textos repetidos por ícones.

## Formulário de venda

- Produto, quantidade e preço unitário aparecem no início.
- Canal, referência, insumos, descontos e custos vêm depois.
- A etiqueta ZPL é a última seção antes da confirmação da venda.
- O ZPL deixa de ser um texto editável. A seção aceita arquivo `.txt` ou `.zpl` por clique ou arrastar e
  soltar; o conteúdo continua sendo lido, validado e salvo da mesma forma.
- Nome do arquivo, pedido, destinatário, cidade e estado continuam visíveis. É possível substituir ou retirar
  a etiqueta antes de salvar.

## Ações das listagens

- Editar, excluir, cancelar, pagar, receber, etiqueta, compra, baixa, ajuste, fotos, importação e envio de
  estoque usam ícones próprios nas tabelas.
- Cada ícone tem nome acessível, texto nativo do navegador e uma explicação curta ao passar o mouse ou focar
  pelo teclado.
- A dica abre alinhada à direita do ícone, para não estourar a tabela. Soltar um arquivo fora da zona
  não faz o navegador abri-lo.
- Os alvos preservam 44 px no celular. Ações destrutivas continuam visualmente distintas.
- Botões de formulário e ações principais fora das linhas continuam com texto, porque nesses pontos o texto
  orienta a tarefa e não polui uma lista repetitiva.

## Compatibilidade

Não há mudança de API, banco, cálculo, estoque ou Caixa. A etiqueta já persistida pela spec 032 continua
compatível e pode ser substituída pelo novo campo de arquivo.

## Aceitação

Conferir upload por clique e por arrastar, ausência do código ZPL editável, ordem do formulário e leitura
automática do pedido. Em todas as tabelas com ações, conferir ícone específico, explicação no mouse, foco por
teclado, nome acessível e funcionamento original. Rodar typecheck, build e suíte completa do backend.
