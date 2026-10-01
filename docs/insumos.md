# Insumos

O que a loja **consome** para fabricar, embalar, enviar e operar: filamento, embalagens, etiquetas de
impressora, fita, cola, verniz, lixa, ferramentas. Fica em **/jalapao-store/insumos**, atrás do login.

> Insumo **não é produto**: não tem SKU nem preço de venda e nunca aparece em Vendas, Anúncios ou no
> valor do estoque de produtos. Especificação em [024](specs/024-insumos/spec.md).

## Duas abas

**Cadastro e estoque** — a lista de insumos com categoria, **saldo**, preço do rolo (filamento) e as
ações de cada linha: **Comprar**, **Dar baixa**, **Ajustar** e **Editar**. O botão *Gerenciar
categorias* abre o cadastro das categorias de insumo.

**Compras e movimentos** — as compras (com **Pagar** e **Cancelar**) e o razão de todas as mudanças
de saldo. Nada ali é apagado.

## Categorias

Cadastráveis por você e **separadas das categorias de produto**. As iniciais são Filamentos,
Embalagens, Etiquetas e papelaria, Colas e fitas, Acabamento, Ferramentas e Outros. Categoria não se
apaga: desative. A opção *É de filamento* trava depois do primeiro insumo e é o que liga material,
cor, peso e preço do rolo. A opção **Conta como despesa quando comprado** diz se a compra paga daquela
categoria entra como despesa no **Resultado do negócio** ([caixa](caixa.md)): vem desligada em Filamentos,
Acabamento e Colas e fitas, cujo custo já está no custo da peça, e ligada nas outras. Você muda quando
quiser, e vale também para o passado.

O material (PLA, PETG…) é um **campo do filamento**, não uma subcategoria. A lista traz sugestões
(PLA, PLA+, PETG, ABS, ASA, TPU…) e aceita outro valor digitado.

## Filamento: preço por grama e peça multicolor

O preço por grama é `preço do rolo ÷ peso do rolo` (R$ 100,00 por 1.000 g = R$ 0,10 por grama) e o
preço por kg é esse valor × 1.000. A tela mostra os dois. Na categoria de produção 3D, a peça pode ter
**várias linhas de filamento**, uma por cor, com as gramas de cada uma: o custo do filamento é a soma
das linhas. O preço de cada linha é **copiado** ao salvar; se o filamento ficar mais caro depois, a
peça não muda sozinha, só aparece o aviso. Ver [custo de impressão 3D](custo-impressao-3d.md).

## Estoque: rolos e unidades inteiras, sem custo médio

O saldo é um número inteiro (rolos, pacotes, unidades) e nunca fica negativo. Ele **só muda por quatro
caminhos**, todos gravados no histórico com o motivo e quem fez:

| Caminho | O que faz |
|---|---|
| **Comprar** | Entra no saldo na hora e fica **a pagar**. |
| **Dar baixa** | "Usei 1 rolo": tira do saldo, com motivo. |
| **Ajustar** | Corrige para mais ou para menos (contagem, perda), com motivo. |
| **Cancelar compra** | Desfaz uma compra lançada errada (abaixo). |

**Não há desconto automático por produção**: usar um rolo na impressão é uma baixa que você lança. Caixa e
etiqueta podem dar baixa junto com a venda (ver abaixo). O estoque de insumo guarda só a quantidade, **sem custo médio** e sem valor de estoque; o custo
que vale para o lucro vem do preço por grama do filamento escolhido na peça. Insumo inativo não recebe
entradas, mas ainda dá baixa no que sobrou.

## Comprar e pagar

1. **Comprar** pede quantidade, custo unitário (o preço do rolo, no filamento), data, fornecedor e
   referência. O saldo sobe na hora e a compra fica *a pagar*.
2. **Pagar**, na aba Compras e movimentos, pede a data do pagamento (não pode ser futura) e gera **uma**
   saída no caixa com o total, uma única vez. Sem pagar, o caixa não é tocado.
3. Comprar **filamento** atualiza o **preço do rolo** do cadastro para o preço pago (o último preço
   pago). Peças já salvas não mudam.

## Cancelar uma compra lançada errada

O botão **Cancelar** não apaga: a compra fica no histórico como *Cancelada*, o saldo volta ao que era e,
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
- **O lucro não muda.** O custo do insumo não entra na venda; o lucro continua só com o custo do produto.
- **Não há kit padrão por produto**: você escolhe os insumos em cada venda.
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
| API | `/jalapao-store/backend-api/supply-categories/`, `supplies/`, `supply-receipts/`, `supply-movements/` |
| Insumos na venda | `backend/apps/supplies/services.py` (`consume_supplies_for_sale`, `restore_supplies_for_sale`) e `frontend/src/features/sales/sales-page.tsx` |
| Linhas de filamento da peça | `backend/apps/catalog/models.py` (`PrintingFilament`) |
| Testes | `backend/apps/supplies/tests/` e `backend/apps/catalog/tests/test_filamentos.py` |

Ainda não existe: alerta de pouco estoque, kit padrão por produto e custo de insumo no lucro.
