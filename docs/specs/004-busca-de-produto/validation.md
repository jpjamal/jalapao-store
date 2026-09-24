# Validação

Em 2026-09-23, no ambiente local (`docker compose up`, http://localhost:8080/jalapao-store),
com os 6 produtos legados importados e todos com saldo zero.

## Pelas três telas, no navegador

| Tela | O que foi digitado | O que aconteceu |
|---|---|---|
| Vendas | `luminaria`, sem acento | achou `Luminaria Air FOrm`; ao escolher, preencheu o preço unitário com 69,76 e o bruto virou R$ 69,76 |
| Compras / produção | `shen`, depois ↓ e Enter | selecionou `suporte shenlong` e trouxe o custo sugerido R$ 13,99 |
| Estoque | `ze pil` | achou `Ze pilintra 15cm` entre os seis |

Movimento gravado ponta a ponta pelo estoque: +5 unidades de `Ze pilintra 15cm` a R$ 12,00
com motivo preenchido. Resultado conferido na mesma tela — saldo 5, valor a custo R$ 60,00,
custo médio R$ 12,00 — e o formulário voltou vazio, com o campo de produto limpo. É o que
prova que a troca de `form.reset()` por estado funcionou.

## Regras preservadas
- Vendas e compras seguem listando só produtos ativos; o ajuste de inventário alcança
  também os desativados, como antes.
- A escolha continua disparando preço sugerido (venda) e custo sugerido (entrada).
- O saldo aparece em cada linha da lista, como no seletor anterior.

## Build
`npm run build` sem erro de TypeScript.

## Limites da evidência
O catálogo de teste tem 6 produtos: o teto de 50 itens e o aviso de "e mais N" não chegaram
a aparecer, foram conferidos apenas por leitura do código. A navegação por teclado foi
exercitada com ↓ e Enter; ↑ e Esc não foram testados no navegador. Não houve conferência
com leitor de tela — a marcação segue o padrão combobox do ARIA, mas isso é promessa, não
evidência. Nada foi publicado na VPS.
