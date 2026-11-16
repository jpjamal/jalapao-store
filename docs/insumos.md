# Insumos

O que a loja **consome** para fabricar, embalar, enviar e operar: filamento, embalagens, etiquetas de
impressora, fita, cola, verniz, lixa, ferramentas. Fica em **/jalapao-store/insumos**, atrás do login.

> Insumo **não é produto**: não tem SKU nem preço de venda e nunca aparece em Vendas, Anúncios ou no
> valor do estoque de produtos. Especificação em [024](specs/024-insumos/spec.md).

## Duas abas

**Cadastro e estoque** — a lista de insumos com categoria, **saldo**, preço do rolo (filamento) e ícones para
**Comprar**, **Dar baixa**, **Ajustar** e **Editar**; passar o mouse mostra o nome da ação. O botão *Gerenciar
categorias* abre o cadastro das categorias de insumo.

**Compras e movimentos** — as compras (com ícones para **Pagar** e **Cancelar**) e o razão de todas as mudanças
de saldo. Nada ali é apagado.

## Categorias

Cadastráveis por você e **separadas das categorias de produto**. As iniciais são Filamentos,
Embalagens, Etiquetas e papelaria, Colas e fitas, Acabamento, Ferramentas e Outros. Categoria não se
apaga: desative. A opção *É de filamento* trava depois do primeiro insumo e é o que liga material,
cor, peso e preço do rolo. A opção **Conta como despesa quando comprado** diz se a compra paga daquela
categoria entra como despesa no **Resultado do negócio** ([caixa](caixa.md)): vem desligada em Filamentos,
Acabamento e Colas e fitas, cujo custo já está no custo da peça, e ligada nas outras. Você muda quando
quiser. A regra é copiada para cada compra quando ela é cadastrada: alterar a opção ou trocar o insumo de
categoria afeta somente compras futuras. O histórico mostra se cada compra conta como despesa.

O material (PLA, PETG…) é um **campo do filamento**, não uma subcategoria. A lista traz sugestões
(PLA, PLA+, PETG, ABS, ASA, TPU…) e aceita outro valor digitado.

## Filamento: preço por grama e peça multicolor

O preço por grama é `preço do rolo ÷ peso do rolo` (R$ 100,00 por 1.000 g = R$ 0,10 por grama) e o
preço por kg é esse valor × 1.000. A tela mostra os dois. Na categoria de produção 3D, a peça pode ter
**várias linhas de filamento**, uma por cor, com as gramas de cada uma: o custo do filamento é a soma
das linhas. O preço de cada linha é **copiado** ao salvar; se o filamento ficar mais caro depois, a
peça não muda sozinha, só aparece o aviso. Ver [custo de impressão 3D](custo-impressao-3d.md).

## Componentes da peça e baixa na produção (spec 041)

LED, parafuso, cabo e base são insumos da categoria **Componentes** (criada sem contar como despesa na compra). Na
peça 3D, a seção **Componentes da peça** diz quantos vão em cada peça; o custo deles entra no custo da peça, como o
filamento. Ao registrar uma **Produção** em Compras e produção, o filamento (gramas × peças, para cima) e os
componentes (quantidade × peças) **saem do estoque de insumos sozinhos**; cancelar a produção devolve. Falta de saldo
não impede a produção: a tela avisa o que faltou. Para lançar peças que já estavam prontas, desligue *Dar baixa nos
insumos da peça*. Ver [spec 041](specs/041-componentes-e-producao-3d/spec.md).

| Onde o insumo entra | Custo vai para | Sai do estoque |
|---|---|---|
| Dentro da peça (filamento, LED, parafuso) | custo da peça | na produção |
| No envio (caixa, saco, etiqueta) | lucro da venda | na venda |

## Estoque: unidades inteiras (filamento em gramas), sem custo médio

> **Custo na venda (spec 040).** Cada insumo tem um **custo unitário**: o da última compra, ou o de um ajuste de
> entrada com custo. Ele não se edita à mão. Parte do saldo pode sair **sem custo** nas vendas (a lista mostra
> "N sem custo" debaixo do saldo): o saldo que existia antes da spec 040, compras de categorias que ainda contam como
> despesa e ajustes de entrada sem custo. Toda saída usa essa parte primeiro. Assim o mesmo custo nunca entra duas
> vezes no Resultado do negócio. Ver [spec 040](specs/040-custo-das-embalagens-na-venda/spec.md).

O saldo é um número inteiro na unidade do insumo (unidade, metro, folha…) e nunca fica negativo. **Filamento é
contado em gramas** desde a spec 041: a compra continua em rolos e entra como rolos × peso do rolo; a tela mostra
"1.640 g (≈ 1,6 rolo)". Escolha como unidade o menor pedaço que você usa inteiro (saco: unidade; plástico bolha:
metro). Ele **só muda por estes caminhos**, todos gravados no histórico com o motivo e quem fez:

| Caminho | O que faz |
|---|---|
| **Comprar** | Entra no saldo na hora e fica **a pagar**. |
| **Dar baixa** | "Usei 3 caixas", "falha de impressão: 80 g": tira do saldo, com motivo. |
| **Ajustar** | Corrige para mais ou para menos (contagem, perda), com motivo. Na entrada aceita um **custo unitário opcional** (embalagem que já estava em casa): entra com esse custo nas vendas, sem mexer no caixa. |
| **Cancelar compra** | Desfaz uma compra lançada errada (abaixo). |
| **Venda** | Embalagens e outros insumos de envio (abaixo). |
| **Produção** | Filamento e componentes da peça 3D (acima). |

O ajuste de filamento é em gramas e não aceita custo (o preço é o do rolo); use-o para acertar o saldo depois de
pesar o rolo. O estoque de insumo guarda só a quantidade, **sem custo médio** e sem valor de estoque. Insumo inativo
não recebe entradas, mas ainda dá baixa no que sobrou.

## Comprar e pagar

1. **Comprar** pede quantidade, custo unitário (o preço do rolo, no filamento), data, fornecedor e
   referência. O saldo sobe na hora, a compra fica *a pagar* e fica registrado se ela conta como despesa
   no Resultado do negócio. Essa classificação não muda depois.
2. **Pagar**, na aba Compras e movimentos, pede a data do pagamento (não pode ser futura) e gera **uma**
   saída no caixa com o total, uma única vez. Sem pagar, o caixa não é tocado.
3. Comprar **filamento** atualiza o **preço do rolo** do cadastro para o preço pago (o último preço
   pago). Peças já salvas não mudam.

## Cancelar uma compra lançada errada

O ícone de **cancelar** não apaga: a compra fica no histórico como *Cancelada*, o saldo volta ao que era e,
se já estava paga, o caixa recebe um **estorno de entrada**. Só vale enquanto a compra for a **última
movimentação daquele insumo**: se já houve baixa, ajuste ou outra compra depois dela, o sistema recusa e
explica, e a correção passa por um ajuste. Se era filamento, o preço do rolo volta ao de antes, **a menos
que você já o tenha editado**. Compra cancelada não pode ser paga.

## Insumos usados numa venda

Em **Vendas → Registrar venda** há a seção **Insumos usados (opcional)**: escolha o insumo (a lista mostra
o saldo) e a quantidade, por exemplo 1 caixa pequena e 2 etiquetas. Ao confirmar a venda, cada insumo dá
**baixa no saldo junto com a venda**, e a movimentação fica ligada a ela.

- **A seção aparece sempre.** Sem nenhum insumo cadastrado ela explica onde cadastrar (Insumos, e uma compra
  para ter saldo); se a lista não puder ser carregada, por exemplo sem permissão, mostra o motivo.
- **Falta de saldo não impede a venda.** O insumo é baixado só até onde tem (nunca fica negativo) e a tela
  avisa o que faltou ("pedido 5, baixado 3"). O pedido e o que foi de fato baixado ficam gravados na venda.
- **Cancelar a venda devolve os insumos**, só o que foi realmente baixado. Cancelar duas vezes não devolve
  duas vezes.
- **O custo sai do lucro da venda (spec 040).** Cada linha guarda quantas unidades saíram sem custo, o custo
  unitário e o total; a venda soma tudo em *custo das embalagens e insumos* e desconta do lucro. Vendas anteriores
  à spec 040 ficam como estavam.
- **Filamento não entra na venda (spec 041)**: ele sai na produção da peça.
- **Embalagem padrão por produto (spec 040).** No cadastro do produto, a seção *Embalagem padrão* diz o que vai em
  cada unidade vendida (ex.: 1 Caixa M + 1 saco). A venda já vem preenchida com o kit × quantidade; mexeu, vale o
  que você escolheu; *Voltar para a embalagem padrão* refaz. A tela mostra o custo estimado antes de confirmar.
- **Vendas importadas do Mercado Livre não baixam insumo**: a baixa continua manual, por *Dar baixa*.
- Informar insumos na venda e cancelar uma venda que baixou insumo exigem a permissão de movimentar o
  estoque de insumos.

## Onde isso vive

| O quê | Onde |
|---|---|
| Telas | `frontend/src/features/supplies/` (`supplies-page.tsx` e `components/`) |
| Modelos | `backend/apps/supplies/models.py` |
| Preço por grama e material | `backend/apps/supplies/domain/pricing.py` |
| Saldo, compra, pagamento e cancelamento | `backend/apps/supplies/services.py` |
| API | `/api/v1/supply-categories/`, `supplies/`, `supply-receipts/`, `supply-movements/` (rede interna; o navegador usa o BFF `/jalapao-store/api/`) |
| Insumos na venda | `backend/apps/supplies/services.py` (`consume_supplies_for_sale`, `restore_supplies_for_sale`) e `frontend/src/features/sales/sales-page.tsx` |
| Linhas de filamento e componentes da peça | `backend/apps/catalog/models.py` (`PrintingFilament`, `PrintingComponent`) |
| Baixa na produção | `backend/apps/supplies/services.py` (`consume_supplies_for_production`, `restore_supplies_for_production`), chamada por `backend/apps/inventory/services.py` |
| Testes | `backend/apps/supplies/tests/` e `backend/apps/catalog/tests/test_filamentos.py` |

Ainda não existe: alerta de pouco estoque e baixa automática de insumo nas vendas importadas do Mercado Livre.
