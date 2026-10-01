# 026 — Categorias nos lançamentos do Caixa e resultado do negócio

> **Situação: implementada localmente (01/10/2026).** Decisões do dono: o que já está no custo da peça
> não vira despesa (filamento e energia); compra de insumo conta como despesa **conforme a categoria do
> insumo** (opção por categoria); lançamentos manuais antigos ficam em "A classificar".

## Objetivo

Hoje o lançamento manual do Caixa só tem tipo (entrada ou saída), valor, data e descrição. Não dá para
saber quanto se gastou com energia, impostos ou divulgação, e o painel não consegue mostrar o resultado
do negócio, que é o **lucro real das vendas menos as despesas**. Esta spec dá **categoria** a todo
lançamento do Caixa, cadastrável pelo dono, e usa essa categoria para somar as despesas e calcular o
resultado.

## Categorias do Caixa

- Cadastráveis pelo dono, **separadas** das categorias de produto e de insumo.
- Campos: nome (único, sem diferenciar maiúscula ou acento), **direção** (entrada, saída ou ambas),
  **conta no resultado** (sim ou não) e ativa ou inativa. Não se apaga: desativa.
- **Conta no resultado** é o que separa despesa de movimentação de dinheiro. Impostos, divulgação, frete e
  as demais despesas contam; empréstimo recebido, parcela de empréstimo, aporte e retirada do dono **não**
  contam, porque não são receita nem despesa da loja. **Energia** também começa sem contar, porque a energia
  estimada já está no custo da peça (ver "Decisões em aberto").
- **Categorias do sistema**, criadas pela migração e usadas só pelos lançamentos automáticos (o dono não as
  escolhe nem as altera): Venda recebida, Estorno de venda, Compra de produtos, Estorno de compra de
  produtos, Compra de insumos, Estorno de compra de insumos e **A classificar**. Nenhuma delas tem a marca
  "conta no resultado": venda, custo do produto e estoque já aparecem no lucro real, e o **insumo é tratado à
  parte**, pela opção da categoria dele (ver "Resultado do negócio").
- **Categorias iniciais do dono** (podem ser renomeadas, desativadas e acrescidas):

| Categoria | Direção | Conta no resultado |
|---|---|---|
| Energia | saída | **não** (a energia estimada já está no custo da peça) |
| Internet e telefone | saída | sim |
| Impostos e taxas | saída | sim |
| Frete e envio | saída | sim |
| Divulgação | saída | sim |
| Equipamentos e manutenção | saída | sim |
| Outras despesas | saída | sim |
| Outras receitas | entrada | sim |
| Empréstimo recebido | entrada | não |
| Pagamento de empréstimo | saída | não |
| Aporte do dono | entrada | não |
| Retirada do dono | saída | não |

- **Aporte do dono** é dinheiro seu que entra na loja (não é venda nem lucro); **Retirada do dono** é dinheiro
  que sai da loja para uso pessoal (não é despesa do negócio, é o lucro sendo levado). As duas movimentam o
  saldo do Caixa, mas ficam fora do resultado. O empréstimo funciona do mesmo jeito.

- A **direção** da categoria não muda depois que ela tem lançamentos. Mudar **conta no resultado** vale
  para todos os lançamentos dela, inclusive os antigos, porque o resultado é calculado na hora.

## Regras

**Lançamento manual**
- Passa a exigir **categoria**, e a direção do lançamento tem de combinar com a da categoria. Só aparecem
  categorias ativas e que não sejam do sistema.
- O valor, a data, a descrição e a direção continuam imutáveis (correção por lançamento inverso, regra
  existente). Só a **categoria** de um lançamento manual pode ser trocada depois (reclassificar), com a
  permissão de alterar lançamento do Caixa.

**Lançamento automático**
- Venda recebida, estorno de venda, compra de produto paga e seu estorno, compra de insumo paga e seu
  estorno recebem a categoria do sistema **sozinhos, pela origem**, em qualquer caminho que os crie. A
  categoria deles não muda.

**Lançamentos que já existem**
- Os automáticos vão para a categoria do sistema da origem deles. Os manuais vão para **A classificar**, que **não conta no resultado**: o sistema não adivinha a categoria, e assim nenhum valor entra no
  resultado por engano. O dono reclassifica um por um. A tela do Caixa avisa quantos faltam.

**Resultado do negócio**
- `resultado = lucro real + entradas manuais que contam − saídas manuais que contam`, somando tudo desde o
  começo, como os demais números do painel.
- Compra de **produto** não é despesa: é estoque, e o custo do produto já está no lucro de cada venda.
- Compra de **insumo** conta como despesa, **na data do pagamento**, **se a categoria do insumo estiver com a
  opção "conta como despesa quando comprado"** (campo `counts_as_expense` da categoria de insumo, spec 024);
  o estorno da compra reduz a despesa. Valores iniciais: **conta** em Embalagens, Etiquetas e papelaria,
  Ferramentas e Outros; **não conta** em Filamentos (o custo já está nas linhas de filamento da peça),
  Acabamento e Colas e fitas (cabem nos custos fixos da peça). A opção é editável a qualquer momento e vale na
  hora, inclusive para o passado; categoria de insumo nova nasce contando.
- Empréstimo, aporte e retirada não entram no resultado, mas continuam no saldo do Caixa.

## Telas

- **Caixa**: o formulário de lançamento manual ganha **Categoria** (filtrada pela direção escolhida); a
  lista ganha a coluna **Categoria** e um filtro por categoria; um resumo mostra **entradas e saídas por
  categoria**; um botão **Gerenciar categorias** abre o cadastro. A coluna **Origem** passa a mostrar
  também compra de insumo e os estornos (hoje o pagamento de insumo aparece como "Manual").
- **Tela inicial**: novo cartão **Resultado do negócio**, ao lado de Lucro previsto e Lucro real, e um aviso
  quando houver lançamentos **a classificar**.

## Não objetivos

Resultado por período ou por mês, gráficos, orçamento por categoria, anexar comprovante, reclassificar
lançamentos automáticos, apagar lançamentos, imposto sobre vendas e depreciação de equipamentos. A
tela do Caixa continua sem filtro de datas.

## Decisões em aberto

Nenhuma. Decidido pelo dono: vale a regra única **"o que já está no custo da peça 3D não vira despesa no
resultado"**. O custo de cada peça inclui o filamento (linhas de filamento) e uma energia **estimada**; por
isso a compra de filamento e a categoria **Energia** começam como **não contando**. O preço dessa escolha é
que a conta de luz real não aparece no resultado, só a energia estimada nas peças; se a conta for bem maior
do que as peças estimam, o dono liga **Energia** como "conta no resultado" e isso vale na hora, inclusive
para o passado. O custo da peça (filamento, energia, mão de obra, custos fixos) **não muda**: ele segue
servindo para o lucro por peça, o preço sugerido e o valor do estoque, e as vendas antigas não são
reescritas.

Decididos: compra de insumo comum conta como despesa no pagamento; **filamento fica fora da despesa**
(o custo dele já está no custo da peça e contar de novo descontaria duas vezes); as categorias
**Aporte do dono** e **Retirada do dono** ficam como propostas; lançamentos manuais antigos ficam em
**A classificar** até serem reclassificados.

## Validação

Testar categorias (criar, nome repetido sem diferenciar acento, trava da direção, sem DELETE, sistema não
selecionável), lançamento manual exigindo categoria de direção compatível, reclassificar só a categoria,
recusa de mudar valor, data ou descrição, categoria automática atribuída por origem em venda recebida,
estorno, compra de produto, compra de insumo e seus estornos, migração dos lançamentos existentes (origem →
categoria do sistema, manual → A classificar), resultado do negócio (despesa que conta, insumo de categoria que conta e de categoria que não conta, estorno de
insumo reduzindo a despesa, mudar a opção da categoria refletindo no cálculo, empréstimo e retirada que não contam, categoria a classificar fora, mudar "conta no resultado" refletindo no cálculo), contagem de
lançamentos a classificar, origem exibida na tela, permissões e ausência de migrações pendentes.
