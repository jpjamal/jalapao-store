# Validação

## Automatizada (05/11/2026)

- `npm run typecheck`: aprovado.

## Conferência numérica contra o site

Mesmos dados nos dois lugares (site aberto no navegador do aplicativo; `lib/roas.ts` executado em Node):

| Caso | Lucro | Empate | Visibilidade | Rentabilidade | Atual | Classificação |
|---|---|---|---|---|---|---|
| compra 20, operação 3, venda 80, taxa 14% + 16, imposto 4%, frete 5, gasto 6 | 21,60 | 3,70 | 7,41 | 37,04 | 13,33 | Visibilidade 50% |
| compra 10, operação 2, venda 60, taxa 20% + 4,50, sem imposto/frete/gasto | 31,50 | 1,90 | 3,81 | 19,05 | — | — |
| compra 30, operação 5, venda 50, taxa 20% + 4,50, imposto 6%, frete 8, gasto 2 | −10,50 | (site: −4,76) | (site: −9,52) | (site: −31,75) | 25,00 | Perdendo |

Iguais, exceto o ROAS com lucro negativo, que aqui aparece como "—" de propósito.

## Conferência da tela (cópia local)

- Preenchimento manual deu os mesmos números; "Shopee" com venda de R$ 80 preencheu 14% e R$ 16,00 e travou
  os campos; "Mercado Livre Premium" com venda de R$ 60 preencheu 17,5% e R$ 6,50; custo alto mostrou o aviso
  de "sem lucro".
- Não conferido: o celular.

## Publicação

Publicada em 05/11/2026 em https://jpsys.duckdns.org/jalapao-store (e pelo IP).

Pendente: conferir em produção, logado, e no celular.
