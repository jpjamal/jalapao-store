# 032 — Etiqueta confiável e ZPL salvo na venda

Pedido do dono: corrigir nomes de arquivo que às vezes usam outro nome ou perdem destinatário e cidade,
incluir o número do pedido no nome do PDF e guardar o ZPL na venda para baixar ou imprimir a etiqueta
novamente pelo histórico.

## Comportamento

- A ferramenta compara leituras de mais de uma região da etiqueta. O conjunto nome, CEP, cidade e estado
  é escolhido em conjunto, dando preferência ao bloco identificado como destinatário e sem misturar dados
  de CEPs diferentes.
- O número do pedido, quando localizado, passa a abrir todo nome automático de PDF. O usuário continua
  podendo corrigir manualmente o nome no cartão antes de baixar.
- No cadastro da venda é possível escolher um `.txt` ou colar o ZPL. O navegador renderiza e lê a etiqueta;
  o pedido preenche automaticamente **Referência / número do pedido** enquanto esse campo não tiver sido
  preenchido manualmente.
- Pedido, destinatário, cidade e estado lidos ficam visíveis e editáveis antes de salvar. Esses dados e o ZPL
  original ficam ligados à venda para que uma correção seja preservada nas próximas gerações.
- O histórico oferece **Adicionar etiqueta** nas vendas antigas e **Etiqueta** nas que já têm ZPL. A janela
  permite substituir, baixar o PDF e abri-lo para impressão.
- A etiqueta não participa dos cálculos da venda, estoque, lucro, recebimento ou Caixa. Excluir logicamente
  a venda mantém seu histórico interno; uma venda excluída não aceita etiqueta nova.

## Segurança e limites

- A listagem de vendas informa apenas se há etiqueta e seu pedido; o ZPL, que contém dados pessoais, só é
  devolvido pela rota autenticada da etiqueta de uma venda específica.
- O limite é 5 MB de ZPL. A API rejeita conteúdo sem `^XA` e `^XZ` e caracteres nulos.
- Labelary e Tesseract continuam necessários no navegador para renderizar e ler imagens ZPL da Shopee.
  Se a leitura não for perfeita, os campos editáveis permitem corrigir antes de salvar ou baixar.

## Aceitação

Validar layouts com cidade acima do CEP, cidade/UF na mesma linha, campos rotulados e CEP com `O` lido no
lugar de zero. Testar criação de venda com ZPL, preenchimento automático da referência, correção manual,
adição posterior, proteção por permissão, regeneração do PDF, nome com pedido e ausência do ZPL na listagem.
Executar suíte completa em PostgreSQL, OpenAPI, typecheck e build.
