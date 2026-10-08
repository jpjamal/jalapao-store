# 031 — Classificação histórica das compras de insumo

Pedido do dono após a auditoria dos cálculos do Caixa: impedir que mudanças posteriores no cadastro
reclassifiquem compras antigas de insumo no Resultado do negócio.

## Comportamento

- Ao cadastrar uma compra, copiar para ela a opção **Conta como despesa quando comprado** vigente na
  categoria do insumo.
- A cópia é histórica e imutável. Alterar a opção da categoria ou mover o insumo para outra categoria
  afeta somente as próximas compras.
- Uma compra ainda não paga conserva sua classificação desde o cadastro. Quando paga, o Resultado do
  negócio usa essa classificação; ao cancelar, o estorno usa exatamente a mesma.
- Compras existentes na publicação recebem a regra atual de sua categoria. A migração não altera o
  saldo do Caixa, estoque, pagamentos, estornos ou valores das compras.
- O histórico de compras informa se cada registro conta como despesa no Resultado do negócio.
- Categorias manuais do Caixa continuam com o comportamento atual: mudar **Conta no resultado** pode
  reclassificar seus próprios lançamentos manuais antigos.

## Aceitação

Testar compra que conta e que não conta, alteração da opção após a compra, troca de categoria do insumo,
compra futura após a alteração, pagamento, estorno e migração dos registros existentes. Validar em
PostgreSQL, contrato da API, tipos e build do frontend.
