# Produtos

O catálogo da loja: o que existe para vender, quanto custa e quanto tem guardado.
Fica em **/jalapao-store/produtos**, atrás do login.

> Até 23/09/2026 isto era uma lista em arquivo JSON, editada por uma página estática
> com senha própria. Agora é tabela em PostgreSQL, com login e permissões do Django.
> O sistema antigo está em `site/` e `api/`, guardado só para consulta e rollback.

## O que é um produto

Dois tipos, e a diferença está em como o custo aparece:

- **Revenda** — você digita o custo e o preço de venda.
- **Impressão 3D** — você informa os parâmetros da peça (filamento, peso, consumo,
  tempo, energia, mão de obra, custos fixos e margem) e o sistema calcula custo e
  preço sugerido, com a mesma conta da ferramenta de impressão 3D.

Todo produto tem um **código (SKU)** único. Os que vieram do sistema anterior guardam
o identificador antigo em `legacy_id` — por isso uma reimportação nunca duplica nem
sobrescreve o que você editou depois.

## Três custos diferentes, e quando cada um vale

É a parte que mais confunde, então vale devagar:

| Custo | O que é | Onde manda |
|---|---|---|
| **do cadastro** | o que você estima que a peça custa | vira sugestão ao registrar uma entrada |
| **da entrada** | o que você realmente pagou naquele lote | forma o custo médio |
| **médio do estoque** | valor guardado ÷ quantidade guardada | é o que sai na venda |

Mexer no cadastro **não** muda o custo das unidades que já estão no estoque. Se o
filamento subiu, isso entra na próxima compra ou produção — não reescreve o passado.

E o lucro de uma venda usa o custo **congelado no momento da venda**. Comprar mais caro
depois não muda o lucro de uma venda antiga.

## Como usar

1. **Produtos → Novo produto**: nome, código e tipo. Se for impressão 3D, os parâmetros
   da peça.
2. O estoque começa em **zero** — quantidade não se digita no cadastro, entra por
   **Compras / produção**.
3. Para vender, o produto precisa estar **ativo** e ter saldo.

Produto que já participou de venda ou movimento **não pode ser apagado**: o banco protege
o histórico com `PROTECT`. Para tirar de circulação, desmarque *ativo* — ele some das
telas de venda e continua nos relatórios.

## Pela ferramenta de impressão 3D

Em **Ferramentas → Impressão 3D** você faz a conta de uma peça e, se gostar do resultado,
dá um nome e clica em **Salvar produto**. Ele entra no catálogo como tipo impressão 3D,
com esses parâmetros e estoque zero.

## Busca e listagem

Busca por nome e código, paginação de 100 em 100. Cada linha mostra quantidade, custo
médio, preço e situação.

## Onde isso vive

| O quê | Onde |
|---|---|
| Tela | `frontend/src/app/(store)/produtos/page.tsx` |
| Modelo | `backend/apps/catalog/models.py` — `Product`, `PrintingProfile` |
| Conta do 3D | `backend/apps/catalog/domain.py` e `frontend/src/lib/ferramentas/custo3d.ts` |
| API | `/jalapao-store/backend-api/products/` |
| Importação do legado | `backend/apps/catalog/management/commands/import_legacy.py` |

Ver também [custo de impressão 3D](custo-impressao-3d.md),
[estoque e custo médio](specs/002-stock-cost/spec.md) e [arquitetura](architecture.md).
