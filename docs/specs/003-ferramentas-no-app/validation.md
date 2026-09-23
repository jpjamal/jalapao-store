# Validação

Em 2026-09-23.

## As contas não mudaram

Os módulos portados foram compilados e comparados, caso a caso, com o JavaScript original
de `site/`. Em todos, **todos os campos do resultado saíram idênticos** — não só o total:

| Caso | Custo | Preço |
|---|---|---|
| 45 g, 115/kg, 200 W, 5 h 18, kWh 1,56, margem 100% | 6,828600 | 13,657200 |
| 80 g, 115/kg, 200 W, 4 h 25, kWh 1,57, margem 100% | 10,586833 | 21,173667 |
| 150 g, 115/kg, 198 W, 14 h, kWh 1,67, mão de obra 13 | 34,879240 | 69,758480 |
| 12,5 g com vírgula decimal, 0 h 47, margem 60% | 8,715870 | 13,945392 |
| tudo em branco | 0 | 0 |

O mesmo cálculo no backend (`apps/catalog/domain.py`) devolve 6,83 / 13,66, 10,59 / 21,17 e
34,88 / 69,76 — os mesmos números com o arredondamento de centavos que só o backend aplica.
Tela e catálogo continuam concordando.

Faixas da Shopee conferidas nos dois lados de cada borda — 1, 8,99, 9, 20, 79,99, 80, 99,99,
100, 199,99, 200, 499,99, 500 e 1200 — com alíquota, taxa fixa e nome da faixa iguais. Venda
completa de R$ 79,99 com custo R$ 20 e recarga de 3%: taxas 20,4980, recarga 2,3997,
depósito 57,0923 e lucro 37,0923, iguais à conta original.

## Testes e build

- `ruff check`, `manage.py check`, `makemigrations --check` e `spectacular --validate
  --fail-on-warn` sem avisos, com o campo `certificate` já no contrato.
- Suíte contra PostgreSQL 17 real: **25 testes, todos passando**, incluindo os 4 de
  concorrência e os 3 novos do certificado.
- Certificado: um autoassinado de 30 dias não alerta; visto a 29 dias de distância, alerta.
  Caminho inexistente devolve `None` e o dashboard responde 200 do mesmo jeito.
- `npm run build`: TypeScript sem erro, com as rotas `/ferramentas/calculadora`,
  `/ferramentas/etiquetas` e `/ferramentas/impressao-3d` geradas.

## Limites da evidência

O OCR não foi reexecutado com etiquetas reais nesta revisão: o código foi portado sem
alterar recortes, limiares nem regras de nome, mas quem confirma a leitura é uma etiqueta
de verdade. O mesmo vale para a renderização no Labelary, que depende de serviço externo.
A conferência do alerta de certificado usou certificado autoassinado, não o de produção.
Nenhuma transação de teste foi criada na VPS.
