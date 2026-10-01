# Validação

Em 01/10/2026:

- Suíte completa (293 testes, 28 deles novos) contra PostgreSQL 17 real, sem nenhum teste pulado: OK. Os 265
  testes que já existiam continuam passando, inclusive os de venda, compra, insumos e do painel. `ruff`,
  `manage.py check`, contrato OpenAPI validado com `--fail-on-warn`, ausência de migrações pendentes,
  `tsc --noEmit` e `next build`: OK.
- Domínio: origem de cada ligação (venda, estorno de venda, compra, estorno de compra, insumo, estorno de
  insumo, manual), chave da categoria do sistema e compatibilidade de direção.
- API de categorias: criar, nome único sem diferenciar acento ("Água e esgoto" contra "ÁGUA E ESGOTO"),
  categoria do sistema só leitura (editar dá 400) e filtros `system`, direção trava depois do primeiro
  lançamento, sem DELETE (405), a marca "conta no resultado" muda mesmo com lançamentos, contagem de lançamentos
  por categoria e permissões (403 sem elas).
- Lançamento manual: exige categoria (sem ela 400), direção incompatível, categoria do sistema e categoria
  inativa recusadas; categoria "entrada ou saída" serve para as duas; a resposta traz `category_name` e `origin`.
  Reclassificar (PATCH): só a categoria muda; valor, descrição, direção e data dão 400 e o lançamento não
  muda; lançamento automático não se reclassifica; PUT dá 405; não se reclassifica para categoria do sistema
  nem de outra direção. `cash/summary/` soma entradas e saídas por categoria, sempre com duas casas.
- Categoria automática por origem, nos caminhos reais: venda recebida e estorno, compra de produto paga e
  estorno, compra de insumo paga e estorno.
- Resultado do negócio: sem nada é zero; só categorias que contam entram (imposto sim; energia, empréstimo e
  retirada do dono não; "outras receitas" sim) e o saldo do Caixa soma tudo; mudar "conta no resultado" muda
  também o passado; lançamento em "A classificar" fica de fora e é contado, e some da contagem quando
  reclassificado; categoria do sistema não conta mesmo com a marca ligada. Insumos: só pagamento de categoria que
  conta entra; compra não paga não entra; estorno reduz a despesa; mudar `counts_as_expense` muda o passado;
  categoria de insumo nova conta por padrão.
- Migrações de dados (com banco de verdade): lançamentos existentes por origem (recebimento de venda, estorno de
  venda, manuais em "A classificar"), as 7 categorias do sistema e as iniciais (Energia e Retirada do dono sem
  contar, Impostos e taxas contando); e a opção dos insumos desligada só em Filamentos, Acabamento e Colas e
  fitas.
- Na tela, com o app local: migração aplicada no banco de desenvolvimento (lançamentos automáticos nas categorias
  do sistema, as de insumo com os valores iniciais); a tela do Caixa mostrou o aviso de 1 lançamento em "A
  classificar", o resumo por categoria, a coluna Origem e o seletor de categoria só nos manuais; reclassificar o
  de R$ 60,00 para "Impostos e taxas" levou o Resultado do negócio de R$ 20,00 para R$ −40,00 e o aviso sumiu,
  sem mudar o saldo; o formulário com "Entrada" listou só categorias de entrada e um aporte do dono de
  R$ 100,00 subiu o saldo e **não** mexeu no resultado; uma compra paga de embalagem (5 × R$ 7,00) reduziu o
  resultado em R$ 35,00 e a de filamento (R$ 90,00) não; ligar "conta como despesa" em Filamentos levou o
  resultado de −75 para −165 e desligar o devolveu a −75; a tela inicial mostrou Lucro previsto, Lucro real,
  Resultado do negócio e Saldo de caixa.
- Os lançamentos, insumos e o usuário criados no teste foram removidos do banco local.

## Limites da evidência
Conferido por automação no painel do navegador (cliques por script, porque o painel ficou oculto), sem celular
nem tema escuro e sem usuário que não seja superusuário na tela (as permissões foram testadas na API). Em
produção os lançamentos manuais que já existem ficam em "A classificar" até o dono classificá-los. O Resultado
do negócio é de tudo desde o começo, sem filtro por período.
