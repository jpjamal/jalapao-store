# Plano

Em `frontend/src/features/listings/listings-page.tsx`: `upload(files[])` envia em fila e junta os avisos;
o `<input>` ganhou `multiple` e a área aceita `drop`. A reordenação usa o arrastar nativo do navegador no
`<li>` da foto usada (`draggable`, `onDragStart/Over/Drop/End`), com a função `reordenar(id, alvo)` sobre a
lista `selected`, que já é a ordem do anúncio. `exibidas` coloca as usadas primeiro, na ordem de `selected`.
