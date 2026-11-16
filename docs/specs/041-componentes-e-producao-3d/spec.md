# 041 — Componentes da peça 3D, filamento em gramas e baixa na produção

Pedido do dono (16/11/2026): a peça 3D não usa só filamento. A luminária leva LED, outras levam parafuso,
cabo, base. Como controlar esses insumos, tanto no custo quanto no estoque, sendo que filamento, embalagem e
componente são todos insumos e só mudam de categoria e de unidade? Proposta discutida e aprovada pelo dono na
mesma conversa.

## A ideia

Todo insumo é igual. O que muda é **onde ele entra**, e isso decide para onde vai o custo e quando ele sai do
estoque:

| | Composição (vai dentro da peça) | Embalagem de envio (spec 040) |
|---|---|---|
| Exemplos | filamento (g), LED, parafuso, cabo, base | caixa, saco, fita, etiqueta |
| Custo vai para | o **custo do produto** (e o preço sugerido) | o **lucro da venda** |
| Sai do estoque | ao **registrar a produção** | ao **registrar a venda** |
| Varia caso a caso? | não: a luminária sempre leva 2 LEDs | sim: na venda dá para trocar ou tirar |

## Antes

- A peça 3D tinha só linhas de filamento (spec 024). LED e parafuso não entravam no custo da peça.
- O filamento era contado em **rolos inteiros**. Não havia como tirar 120 g por peça; a baixa era manual quando o
  rolo acabava.
- A entrada de **Produção** (Compras e produção) só aumentava o estoque do produto; não tocava nos insumos.
- Filamento podia ser escolhido entre os insumos da venda (saía sem custo).

## Agora

1. **Componentes da peça.** No cadastro do produto 3D e na ferramenta *Custo de impressão 3D*, a seção
   **Componentes da peça** lista insumos que não são filamento, com a quantidade por peça. O custo unitário é
   **copiado** do insumo quando a linha é salva (como o preço do rolo no filamento); se o insumo mudar de custo, a
   peça não muda sozinha: aparece o aviso e a opção "usar o custo atual". O custo dos componentes entra no custo da
   peça **antes da margem**:
   `custo = filamento + componentes + energia + mão de obra + custos fixos`.
2. **Filamento em gramas.** O saldo do filamento passa a ser contado em gramas. A **compra continua em rolos** (é
   como se compra) e entra no saldo como `rolos × peso do rolo`; cancelar a compra tira exatamente o que ela pôs.
   Baixa e ajuste de filamento são em gramas e não aceitam custo (o preço é o do rolo). A unidade do filamento é
   sempre "g". A tela mostra "1.640 g (≈ 1,6 rolo)".
3. **Produção dá baixa nos insumos.** Registrar uma entrada de **Produção** de N peças tira do estoque de insumos:
   - o filamento de cada linha: `gramas × N`, arredondado para cima;
   - cada componente: `quantidade × N`.
   Antes de confirmar, a tela mostra o que vai sair. Como na venda, **falta de saldo não impede a produção**: baixa
   até onde tem, grava o pedido e o baixado, e avisa o que faltou.
4. **Sem baixa, quando precisar.** A opção *Dar baixa nos insumos da peça* (ligada por padrão) pode ser desligada
   para lançar peças que já estavam prontas antes, cujo material já saiu do estoque.
5. **Cancelar a produção devolve os insumos** ao saldo (só o que foi baixado; a parte sem custo volta sem custo).
6. **Filamento não sai mais na venda.** Ele sai na produção. A lista de insumos da venda não mostra filamento e a
   API recusa.
7. **Categoria Componentes.** Criada pela migração, **sem** contar como despesa na compra: o custo do LED e do
   parafuso entra pelo custo da peça, e contar na compra seria contar duas vezes.

## Decisões

- **Produção, e não venda, é o momento da baixa da composição.** A venda exige estoque do produto, então toda peça
  vendida passou antes por uma entrada (produção). Peça feita sob encomenda: registre a produção de 1 unidade e
  depois a venda. Por isso a opção "baixar a composição na venda" ficou de fora.
- **Componentes só na peça 3D.** Produto de revenda não é produzido aqui.
- **Peça sem linhas de filamento** (preço por kg e peso digitados à mão) não sabe qual filamento usou: a produção
  baixa só os componentes.
- **O custo da produção continua sendo o informado na entrada** (sugerido pelo custo da peça). A baixa dos insumos
  na produção não mexe em lucro nenhum: o custo deles já está na peça.

## Fora do escopo

- Aviso de pouco estoque de insumo.
- Composição para produtos que não são 3D.
- Baixa da composição em vendas importadas do Mercado Livre.

## Aceitação

- **041-C1** Componentes entram no custo e no preço sugerido da peça (backend e ferramenta dão o mesmo número);
  filamento e componente repetido são recusados como componente; o custo copiado só muda quando o dono pede.
- **041-C2** Compra de filamento entra em gramas (rolos × peso); cancelar tira as gramas; ajuste de filamento é em
  gramas e recusa custo; o cadastro de filamento fica com unidade "g".
- **041-C3** Produção baixa o filamento (gramas × N, para cima) e os componentes (quantidade × N), grava o pedido e o
  baixado e não é impedida por falta de saldo; com a opção desligada, não baixa nada; compra de produto não baixa.
- **041-C4** Cancelar a produção devolve os insumos, inclusive a parte sem custo.
- **041-C5** A migração converte saldo, parte sem custo, histórico e linhas de venda do filamento para gramas, muda a
  unidade para "g" e cria a categoria Componentes sem contar como despesa.
- **041-C6** Filamento não entra nos insumos da venda.
