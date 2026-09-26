# 002 — Compras, produção e custo do estoque

## Comportamento
- Cada entrada registra um produto, origem compra/produção, quantidade inteira positiva,
  custo unitário, data, fornecedor/referência, observação e autor. Um documento com vários
  produtos pode ser lançado em entradas com a mesma referência. Histórico imutável.
- Custo de referência do catálogo continua sendo sugestão para novas entradas, inclusive
  cálculo 3D. Editá-lo não reavalia estoque nem vendas anteriores.
- Valor do estoque é saldo monetário persistido. Entrada soma quantidade × custo informado;
  saída retira proporcionalmente pelo custo médio móvel. Arredondamento HALF_UP em centavos,
  última unidade consome todo o saldo. Média exibida com seis casas; custo total é autoritativo.
- Venda congela o custo total retirado por item; cancelamento devolve exatamente esse custo,
  mesmo depois de compras a preços diferentes. Recebimento continua pelo líquido, sem CMV.
- Compra entra sem movimentar caixa. A ação Pagar registra o total uma única vez, com data
  informada. Produção não permite essa ação: materiais/energia pagos são despesas separadas.
  Não lançar manualmente uma compra que será paga pelo botão, para evitar duplicidade.
- Ajustes de inventário continuam disponíveis: entrada exige custo explícito; saída usa a
  média. Ajuste não gera caixa. Não serve como devolução de compra nem estorno fiscal.
- Chave idempotente impede duplicar entrada em retries; produto bloqueado em transação
  protege quantidade e valor durante compras/vendas concorrentes. Permissões Django.

## Migração e limites
Saldo existente recebe quantidade × custo de referência como avaliação inicial, sem
inventar compras. Movimentos antigos mantêm valor desconhecido (null). Itens de venda
antigos recebem custo total do snapshot já gravado. Não alterar lucro/caixa histórico.
Sem pagamento parcial, contas a pagar completas, FIFO, consumo automático de matéria-prima,
edição/cancelamento de compras ou retroatividade da média. Data é documental; a ordem de
registro determina a média. Correções de quantidade via ajuste justificado; acerto financeiro
via lançamento inverso, preservando o documento original.

## Aceitação
10 unidades a R$10 + 10 a R$14 → 20 un., R$240 e média R$12. Venda de 2 retira R$24;
lucro desconta R$24, caixa recebe somente líquido da venda. Alterar referência não muda
saldo. Cancelar devolve R$24. Pagar duas vezes cria uma saída. Produção não cria caixa.
Entrada inválida/sem permissão não tem efeitos; concorrência e arredondamento conservam valor.

## Contrato da API
Antes em `backend/docs/specs/002-stock-cost.md`, consolidado aqui na spec 017.
- `POST receipts/`: `idempotency_key` UUID, `product_id` UUID, `kind` purchase/production,
  `quantity` 1..1000000, `unit_cost` decimal não negativo, `occurred_on` até hoje,
  `supplier`/`reference`/`notes` opcionais. 201 com o registro e o total. A mesma chave com
  outro conteúdo ou outro autor: 400. Bloqueia o produto, soma valor e quantidade e grava
  Movement e Outbox na mesma transação. Não altera `cost_price` do catálogo.
- `POST receipts/{id}/pay/`: `occurred_on` até hoje; só compra. Idempotente: uma saída no
  caixa, sem nova alteração de estoque.
- Leitura exige `view_receipt`. Sem PATCH/DELETE na API nem edição no Admin.
- Corte da migração: backup e pausa da API antes de migrar; não voltar ao código anterior de
  custos sem restaurar um backup consistente.

## Critérios da interface
Antes em `frontend/docs/specs/002-stock-cost.md`, consolidado aqui na spec 017.
- Menu Compras / produção → `/entradas`, um produto por entrada. O custo de referência é
  sugerido ao escolher o produto e pode ser trocado pelo custo real.
- O total na tela é prévia; quem calcula é o backend. Erros da API visíveis, botão bloqueado
  durante o envio, chave idempotente mantida em nova tentativa e renovada após sucesso.
- Pagar pede data e confirma o total. Produção não oferece pagamento.
- Estoque mostra `stock_value`/`average_cost` do backend; ajuste positivo exige custo. O caixa
  identifica a origem "Compra de estoque"; o catálogo mostra "Custo de referência".
