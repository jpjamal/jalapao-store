# Validação

## Automatizada (16/11/2026)

- `apps/supplies/tests/test_custo_na_venda.py`: 18 testes (compra com e sem despesa, parte sem custo saindo
  primeiro, baixa manual, filamento, cancelar venda, editar venda, custo da compra e do cancelamento, ajuste com e sem
  custo, custo só em entrada, despesa x venda no resultado, API do ajuste, custo não editável, embalagem padrão,
  recusa de filamento e repetido, custo na resposta da venda).
- Dois testes antigos atualizados de propósito: Embalagens não conta mais como despesa (`test_estoque_insumos`,
  `test_migracao_categorias`).
- Suíte completa do backend: 372 testes, OK (6 ignorados, como antes). `makemigrations --check` sem pendência;
  `ruff check` aprovado; `spectacular --validate --fail-on-warn` aprovado e `docs/openapi.yml` regerado.
- Frontend: `tsc --noEmit` e `npm run build` aprovados.

## Ponta a ponta local (banco descartável)

- Depois da migração, Embalagens com "conta como despesa" desligado.
- Caixa M comprada a R$ 2,00 (10 un.) e Saco 20x30 ajustado com custo R$ 0,30 (50 un.): a lista de Insumos mostra
  "Custo unitário" R$ 2,00 e R$ 0,30; o ajuste mostra o campo "Custo unitário — opcional, só para entrada".
- Produto Caneca com embalagem padrão 1 Caixa M + 1 Saco: o formulário mostrou "Custo atual da embalagem: R$ 2,30".
- Nova venda com 2 canecas: os insumos vieram preenchidos (2 caixas, 2 sacos) com "Custo estimado: R$ 4,60".
- Venda gravada: bruto R$ 60,00, custo do produto R$ 10,00, custo dos insumos R$ 4,60, **lucro R$ 45,40**; saldo
  8 caixas e 48 sacos; a janela da venda mostra "Custo das embalagens e insumos R$ 4,60" e o custo de cada linha.

## Não conferido

- Produção e celular.
- Com dados reais: o saldo de embalagens que já existe sai sem custo até acabar (por desenho).
