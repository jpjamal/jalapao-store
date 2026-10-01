# Plano

> Aprovada pelo pedido do dono; ver a [spec](spec.md). Só frontend: a API, os dados e as regras de pagamento não mudam.

**Peças comuns em `shared/`:**
- `components/confirm-dialog.tsx`: `ConfirmDialog`, a janela flutuante, feita com `<dialog>` nativo (`showModal`:
  Esc fecha, o foco fica dentro, o fundo não clica). O erro da ação aparece dentro da janela, porque a página fica
  coberta.
- `components/pay-selection.tsx`: `SelectBox` (caixa que aceita "algumas marcadas"), `PaySelectionBar` (faixa com
  quantidade, total e botões) e `PayDialogBody` (resumo de uma compra ou lista do lote).
- `hooks/use-selection.ts`: guarda os ids marcados, mas só conta quem está nas linhas pagáveis **da tela**; assim
  o que sai da tela (filtro, ordem, página) sai da seleção sem efeito colateral.
- `lib/pay.ts`: `payInOrder` paga uma por vez, na ordem da tela, e para na primeira falha, devolvendo as pagas, as
  que faltam e a mensagem.

**Telas:** `inventory/receipts-page.tsx` e `supplies/components/supply-history.tsx` trocam o formulário de pagamento
por `ConfirmDialog`, ganham a coluna de caixas e a faixa. O estado `paying` passa a ser uma lista (vazia = fechada).
Cada pagamento continua chamando `receipts/<id>/pay` ou `supply-receipts/<id>/pay` com a data de hoje; o
pagamento já é idempotente no backend. Sem endpoint novo, então o BFF não muda.
