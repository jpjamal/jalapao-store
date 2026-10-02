# Caixa e resultado do negócio

O Caixa mostra o dinheiro que **entrou e saiu de verdade**. Fica em **/jalapao-store/caixa**, atrás do
login. Especificação em [026](specs/026-categorias-do-caixa/spec.md).

## O que entra no Caixa

- **Automático:** venda recebida (e o estorno, se cancelada), compra de produto paga (e estorno), compra de
  insumo paga (e estorno). Você não lança nada à mão para isso.
- **Manual:** conta de luz, imposto, empréstimo, aporte e retirada do dono, qualquer outra entrada ou saída.

Lançamento não se apaga nem se edita. Para corrigir valor, data ou descrição, faça um lançamento inverso
com o motivo. **Só a categoria** de um lançamento manual pode ser trocada depois.

## Categorias

Todo lançamento tem categoria. Nos manuais **você escolhe**; nos automáticos o sistema escolhe pela origem,
e elas aparecem como "do sistema" (Venda recebida, Estorno de venda, Compra de produtos, Estorno de compra de
produtos, Compra de insumos, Estorno de compra de insumos). O botão **Gerenciar categorias** cria e edita as
suas. Categoria não se apaga: desative.

Cada categoria tem **direção** (entrada, saída ou ambas), que não muda depois do primeiro lançamento, e a marca
**conta no resultado**. As iniciais:

| Categoria | Direção | Conta no resultado |
|---|---|---|
| Energia | saída | **não** (a energia estimada já está no custo da peça) |
| Internet e telefone, Impostos e taxas, Frete e envio, Divulgação, Equipamentos e manutenção, Outras despesas | saída | sim |
| Outras receitas | entrada | sim |
| Empréstimo recebido | entrada | não |
| Pagamento de empréstimo | saída | não |
| Aporte do dono | entrada | não |
| Retirada do dono | saída | não |

**Aporte do dono** é dinheiro seu que você coloca na loja; **Retirada do dono** é dinheiro que você tira para
uso pessoal. Os dois movimentam o saldo do Caixa, mas não são receita nem despesa do negócio. O empréstimo
funciona do mesmo jeito.

## A classificar

Os lançamentos manuais que já existiam antes das categorias foram para **A classificar**, e o sistema não
adivinha a categoria. Eles **ficam fora do Resultado do negócio** até você escolher a categoria de cada um, na
lista de movimentações (cada lançamento manual tem um seletor de categoria). A tela do Caixa e a tela inicial
avisam quantos faltam.

## Resultado do negócio

Cartão da tela inicial:

```
resultado = lucro real
          + entradas manuais cujas categorias contam
          − saídas manuais cujas categorias contam
          − compras de insumo pagas (menos estornos) de categorias de insumo que contam como despesa
```

- **Lucro real** é o das vendas já recebidas ([lucro real](specs/025-lucro-real/spec.md)).
- **Regra única: o que já está no custo da peça 3D não vira despesa.** O custo da peça inclui o filamento (linhas
  de filamento) e uma energia estimada, por isso a categoria **Energia** e os insumos **Filamentos**,
  **Acabamento** e **Colas e fitas** começam sem contar. Embalagens, Etiquetas e papelaria, Ferramentas e Outros
  contam, porque não estão em custo nenhum.
- **Compra de produto não é despesa**: é estoque, e o custo do produto já está no lucro de cada venda.
- Empréstimo, aporte e retirada não entram, mas estão no saldo do Caixa.
- Tudo desde o começo, como os outros números da tela inicial; não há filtro por período.

Mudar **conta no resultado** de uma categoria do Caixa, ou **conta como despesa** de uma categoria de insumo
([insumos](insumos.md)), vale na hora, **também para o passado**, porque o resultado é calculado a cada vez.
Nada disso muda o saldo do Caixa, o estoque nem o lucro de cada venda.

## Onde isso vive

| O quê | Onde |
|---|---|
| Telas | `frontend/src/features/finance/` (`cash-page.tsx` e `components/`) e o cartão em `features/dashboard/` |
| Modelos | `backend/apps/finance/models.py` (`CashCategory`, `CashEntry.category`) |
| Origem e categorias do sistema | `backend/apps/finance/domain/categories.py` |
| Resultado | `backend/apps/finance/services.py` e `DashboardView` |
| API | `/api/v1/cash/`, `cash/summary/`, `cash-categories/` (rede interna; o navegador usa o BFF `/jalapao-store/api/`) |
| Testes | `backend/apps/finance/tests/` |
