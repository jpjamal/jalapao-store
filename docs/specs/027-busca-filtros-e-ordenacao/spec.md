# 027 — Busca, filtros e ordenação em todas as listagens

## Objetivo

Hoje só algumas telas têm busca, poucas têm filtro e **nenhuma ordena**. O estoque, por exemplo, não permite
procurar nem filtrar. O dono quer, em todas as telas de listagem do sistema, **busca**, **filtros** e
**ordenação por qualquer coluna** (números e textos).

## Como funciona (igual em todas as telas)

- **Busca:** uma caixa de texto no topo da lista procura nas colunas de texto (nome, código, motivo,
  referência…). Ignora maiúscula e, onde o banco permite, acento. Espera o dono parar de digitar (cerca de
  0,3 s) antes de buscar, e volta à primeira página.
- **Filtros:** seletores acima da lista, conforme a tela (categoria, situação, canal, saldo, pagamento, tipo de
  movimento…) e, nas listas de datas, **período** (de / até). Os filtros somam entre si e com a busca. Um botão
  **Limpar filtros** aparece quando há algum ativo.
- **Ordenação:** o **cabeçalho de cada coluna ordenável é clicável**. O primeiro clique ordena de forma
  crescente, o segundo decrescente, o terceiro volta à ordem padrão da tela. Uma seta mostra a coluna e a
  direção ativas. Texto ordena em português (acento e maiúscula não atrapalham, "Álcool" fica junto do "A").
  Números ordenam como número (10 depois de 9), e datas como data.
- **Listas paginadas** (100 por página) ordenam e filtram **no servidor**, para a ordem valer para a lista
  inteira e não só para a página aberta. A ordem inclui sempre um desempate fixo, para uma linha não pular de
  página entre uma consulta e outra.
- **Listas pequenas, carregadas por inteiro** (categorias, rascunhos, lojas e anúncios das integrações, posição
  do estoque) buscam, filtram e ordenam na própria tela.
- Colunas que são só um resumo calculado e não existem no banco (por exemplo, a origem de um lançamento do
  Caixa) não ordenam, e o cabeçalho não é clicável.
- Mudar a busca, um filtro ou a ordem **volta à primeira página**. O estado não é guardado entre visitas.

## Telas e o que cada uma ganha

| Tela | Busca em | Filtros | Ordena por |
|---|---|---|---|
| Produtos | nome, SKU, GTIN, marca, modelo | categoria, situação, estoque (com ou sem saldo) | nome, categoria, custo, preço, estoque, situação |
| Categorias de produto | nome | situação, parâmetros 3D | nome, parâmetros 3D, produtos, situação |
| Estoque: posição atual | nome, SKU | categoria, saldo (com ou sem) | produto, unidades, valor a custo, custo médio |
| Estoque: movimentações | produto, SKU, motivo | tipo (entrada ou saída), período | data, produto, variação, saldo após, variação em R$ |
| Compras e produção | produto, fornecedor, referência, observação | origem, situação, pagamento, período | data, produto, quantidade, custo unitário, total |
| Vendas | referência, pedido, produto | canal, situação, recebimento, período | data, canal, bruto, líquido, lucro, situação |
| Caixa: movimentações | descrição, categoria | tipo, categoria, origem, período | data, descrição, categoria, valor |
| Caixa: por categoria e categorias | nome | situação (nas categorias) | nome, entradas, saídas, lançamentos |
| Insumos | nome, cor, material | categoria, situação, saldo | insumo, categoria, saldo, preço do rolo, situação |
| Insumos: compras | insumo, fornecedor, referência, observação | situação, pagamento, período | data, insumo, quantidade, custo unitário, total |
| Insumos: movimentos | insumo, motivo | tipo, período | data, insumo, variação, saldo depois |
| Categorias de insumo | nome | situação | nome, insumos, filamento, despesa, situação |
| Anúncios: rascunhos salvos | produto, título | canal, situação | produto, canal, título, situação |
| Integrações: lojas e anúncios | loja, título, código | canal, sincronia | colunas da tabela |

A tabela de regras da calculadora de taxas é uma referência fixa, e não uma listagem de dados; não entra.

## Regras

- A ordenação aceita só colunas previstas por tela (lista fechada no backend); qualquer outra é ignorada, sem
  erro e sem expor campo interno.
- A ordem padrão de cada tela continua a de hoje (mais recente primeiro, ou por nome), até o dono clicar.
- Filtro de escolha (tipo de movimento, origem do lançamento) com valor que não existe dá 400 com explicação, e a
  tela mostra o erro como nos demais casos; filtro de sim ou não com valor sem sentido é ignorado.
- **Nada muda nos dados**: só se muda como a lista é consultada e mostrada.

## Não objetivos

Guardar busca, filtro e ordem entre visitas ou na endereço (URL), exportar a lista, busca por vários termos com
operadores, escolher colunas visíveis e filtros salvos.

## Validação

Testar, por tela de servidor: cada coluna da lista de ordenação em crescente e decrescente (incluindo texto com
acento e número), o desempate estável entre páginas, coluna fora da lista ignorada, busca em cada campo
previsto, cada filtro, período (de e até, inclusive o dia inclusivo) e a combinação de busca, filtro e ordem.
Testar os auxiliares de ordenação no frontend (texto com acento, número em texto, data, direção). Conferir na
tela cada listagem: clicar cabeçalhos, digitar na busca, escolher filtros e período e limpar.
