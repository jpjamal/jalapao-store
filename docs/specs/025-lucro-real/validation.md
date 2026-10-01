# Validação

Em 01/10/2026:

- Suíte completa (265 testes, 4 deles novos) contra PostgreSQL 17 real, sem nenhum teste pulado: OK.
  `ruff`, contrato OpenAPI validado com `--fail-on-warn` (só o campo novo `realized_profit`), ausência
  de migrações pendentes, `tsc --noEmit` e `next build`: OK.
- Testes: sem vendas os dois lucros são zero; venda recebida (bruto 60, custo 20) conta nos dois e venda a
  receber só no previsto; a taxa real da plataforma entra no lucro (líquido 25, custo 10, lucro 15); venda
  recebida e depois cancelada não conta em nenhum.
- Na tela, com o app local: com uma venda recebida (lucro R$ 20,00) e outra a receber (R$ 22,00), a tela
  inicial mostrou **Lucro previsto R$ 42,00** e **Lucro real R$ 20,00**, com "A receber R$ 50,00"; depois
  de receber a segunda venda, o real foi a R$ 42,00 e o "a receber" a zero.
- A venda e o usuário criados no teste foram removidos do banco local, e o estoque do produto voltou a 15
  unidades e R$ 210,00.

## Limites da evidência
Conferido por automação no painel do navegador, sem celular nem tema escuro. O lucro real mede o
resultado das vendas já recebidas: não desconta despesas lançadas à mão no Caixa, compras de insumo nem de
estoque (regra existente: o fluxo de caixa manual não altera o lucro das vendas).
