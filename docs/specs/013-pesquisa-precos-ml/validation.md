# Validação

## Automática
138 testes passando (10 novos em `apps/common/test_pesquisa_precos.py`), com o Mercado Livre de
mentira respondendo no formato da documentação:
- preço lido em `price`, `price.amount`, `sale_price.amount` e `buy_box_winner.price`;
- faixa de preços ignora quem veio sem preço;
- produtos com preço vencedor, marca, modelo e frete; sem preço vai para o log;
- ofertas da mais barata para a mais cara, com resumo;
- mais vendidos na ordem, completados por tipo, anúncios numa chamada só;
- consulta não chama nada além de leitura;
- rotas exigem permissão, validam códigos antes de chamar o Mercado Livre e explicam a falta
  de conta;
- cliente real com HTTP gravado: caminhos da documentação e leitura do `/items/bulk`.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## Limites da evidência
Nada foi consultado no Mercado Livre de verdade. O que só a primeira pesquisa real confirma: se
a conta tem acesso a `/products/search` e `/highlights`, o formato real dos preços e se produto
do vendedor vem com preço.
