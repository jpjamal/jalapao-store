# Validação

Em 01/10/2026, no navegador com o app local (`tsc --noEmit` sem erros):

- Compras e produção: o botão Pagar abre a janela no meio da tela; Cancelar e Esc fecham sem pagar; Confirmar paga,
  fecha, a lista mostra "Paga" e a tela rola até o aviso. Só compra confirmada e a pagar tem caixa (paga, cancelada
  e produção não têm). A caixa do cabeçalho marca todas as a pagar e fica "meio marcada" quando só algumas estão.
  A faixa mostra a quantidade e o total; o lote de 4 compras (R$ 45,00) foi pago com uma saída no Caixa por compra,
  sem duplicar, inclusive a que foi paga por fora antes de confirmar (o pagamento repetido é aceito sem nova saída).
- Falha no meio do lote (erro forçado na 2ª de 3): a 1ª ficou paga, a janela continuou aberta só com as 2 que
  faltavam e disse "1 de 3 já foram pagas. Parou em …: erro"; as que faltavam continuaram com "Pagar" na lista.
- Insumos, compras: o lote de 2 compras (R$ 63,00) foi pago; aviso e lista corretos.
- Não conferido: a janela no celular (só o desenho responsivo do `<dialog>`, largura `min(92vw, 26rem)`).
