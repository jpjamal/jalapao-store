# Validação

## Automatizada (16/11/2026)

- `apps/supplies/tests/test_producao.py`: 19 testes (componentes no custo e sem componentes igual; filamento em
  gramas na compra, no cancelamento, no ajuste sem custo e no cadastro; componentes no custo pela API, recusa de
  filamento e de repetido, custo congelado até o dono pedir; produção baixa filamento e componentes, gramas para
  cima, falta de saldo não impede, sem baixa, compra de produto não baixa, cancelar devolve com a parte sem custo,
  produto sem parâmetros 3D, API mostra o que saiu; migração de rolos para gramas e categoria Componentes).
- Dois testes antigos atualizados de propósito: filamento não sai mais na venda (`test_custo_na_venda`) e a
  categoria Componentes aparece nas opções de despesa (`test_migracao_categorias`).
- Suíte completa do backend: 391 testes, OK (6 ignorados, como antes). `makemigrations --check` sem pendência;
  `ruff check` aprovado; `spectacular --validate --fail-on-warn` aprovado e `docs/openapi.yml` regerado (só acréscimos).
- Frontend: `tsc --noEmit` e `npm run build` aprovados.

## Ponta a ponta local (banco descartável)

- Filamento "PLA Preto" com saldo de **2 rolos** antes da migração: depois dela, **2.000 g** (parte sem custo também
  2.000), unidade "g"; categoria Componentes criada sem contar como despesa. A lista de Insumos mostra
  "2.000 g (≈ 2 rolos)".
- LED 001 comprado a R$ 3,50 (10 un.) e Parafuso M3 ajustado com custo R$ 0,10 (50 un.), na categoria Componentes.
- Produto novo pela tela, categoria Produção Impressão 3D: 120 g de PLA, 2 LEDs e 4 parafusos, 2 h a 200 W:
  **custo R$ 20,02 e preço sugerido R$ 40,05** (12,00 + 7,40 + 0,624; margem 100%).
- Compras e produção, Produção de 3 luminárias: a tela mostrou "Vai sair do estoque de insumos: 360 g de PLA Preto,
  6 LED 001, 12 Parafuso M3"; o custo veio R$ 20,02. Depois: PLA 1.640 g, LED 4, parafuso 38.
- Outra produção de 3 com só 4 LEDs: registrada, com o aviso de que faltaram 2 LEDs; cancelada, os saldos voltaram
  (LED 4, PLA 1.640 g, parafuso 38).
- Ferramenta Custo de impressão 3D com 120 g a R$ 100/kg, 2 LEDs, 2 h a 200 W: Filamento R$ 12,00, Componentes
  R$ 7,00, Energia R$ 0,62, custo R$ 19,62, preço sugerido R$ 39,25.

## Não conferido

- Produção e celular.
- Com dados reais: o saldo de filamento em produção vira gramas pelo peso do rolo cadastrado (rolo sem peso usaria
  1.000 g, mas o cadastro de filamento sempre exige o peso).
