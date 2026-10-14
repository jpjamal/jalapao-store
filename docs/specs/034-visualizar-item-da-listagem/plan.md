# Plano

Componente compartilhado `shared/components/detail-dialog.tsx`: `DetailDialog` (`<dialog>` nativo, com
botão Fechar e rodapé de ações), `DetailList` (pares rótulo/valor), `rowOpen` (propriedades da `<tr>`
clicável) e `RowTitle` (texto principal como botão). `ListAction` ganhou `showText` para o botão com texto
na janela. Em cada página, as ações da linha viraram uma função `xxxActions(item, text)` usada pela tabela
(`text=false`) e pela janela (`text=true`).
