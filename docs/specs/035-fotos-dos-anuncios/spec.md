# 035 — Fotos dos anúncios: várias de uma vez e ordem por arrastar

Pedido do dono: na tela de Anúncios as fotos entravam uma de cada vez, e a ordem só mudava pelas setas.

## Várias fotos de uma vez

- O botão "Adicionar fotos do produto" aceita escolher várias fotos juntas, e a área também recebe fotos
  arrastadas do computador. Formatos aceitos: JPG, PNG e WebP, até 10 MB cada.
- O servidor continua recebendo **uma foto por pedido** (`POST /api/product-images`): o front envia as
  escolhidas em fila, na ordem em que vieram. Todas entram marcadas como usadas no anúncio.
- Se uma falhar, as outras seguem; o aviso lista as que falharam e o motivo. Arquivo que não é JPG, PNG ou
  WebP é ignorado, com aviso. A mensagem de sucesso diz quantas fotos entraram.

## Ordem por arrastar

- No computador, a foto usada no anúncio é arrastada sobre outra foto usada e passa a ocupar a posição dela
  (as demais deslizam). A primeira é a capa. A foto sobre a qual se arrasta ganha um contorno.
- As fotos usadas aparecem primeiro, na ordem do anúncio; as não usadas vêm depois. Assim mudar a ordem
  muda também a posição dos cartões, e não só o número no selo.
- Fotos não usadas não são arrastáveis (toque nelas para usar). As setas continuam existindo, para o teclado
  e para o celular, onde o arrastar do navegador não funciona.
- A ordem só vale no anúncio depois de **Salvar o rascunho**, como antes.

## Compatibilidade

Só apresentação: sem mudança de API, banco ou contrato. A lista `image_ids` do rascunho já guardava a
ordem.

## Aceitação

Escolher 3 ou 4 fotos juntas e ver todas entrarem; soltar fotos na área; arrastar a 3ª foto para a primeira
posição e ver a capa mudar; setas ainda movem; salvar e reabrir o rascunho mantém a ordem.
