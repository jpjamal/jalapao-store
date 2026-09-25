# Validação

## Automática
150 testes passando (13 novos em `apps/common/test_pedidos_ml.py`), com pedidos no formato da
documentação:
- prévia de pedido novo: bruto, taxa pelo `marketplace_fee`, frete pelo `senders`, líquido; não
  cria nada;
- taxa cai para `sale_fee × quantidade` quando o pagamento não traz a comissão;
- anúncio sem vínculo fica pendente; frete não lido vira aviso;
- importar cria a venda do canal Mercado Livre com `external_id`, baixa o estoque e deixa a
  receber;
- o mesmo pedido nunca vira duas vendas, nem repetido na mesma chamada;
- pedido cancelado cancela a venda importada e devolve o estoque;
- sem estoque, falha com motivo e nada muda;
- os números vêm de uma nova busca do pedido;
- rotas exigem permissão e validam os códigos; canal Site Jalapão disponível;
- cliente real com HTTP gravado: caminhos da documentação.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## Limites da evidência
A loja ainda não teve venda no Mercado Livre, então nada foi importado de verdade. O que só a
primeira venda confirma: se `marketplace_fee` vem no pagamento, se `/shipments/{id}/costs`
responde para esta conta e o formato de `senders`.
