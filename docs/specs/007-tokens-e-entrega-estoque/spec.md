# 007 — Tokens protegidos e entrega de estoque por anúncio

## Problema

Tokens de Shopee e Mercado Livre ficam legíveis no banco. A fila atual marca uma mudança de estoque como entregue para todos os canais ao processar uma única conta e pode reenviar uma quantidade antiga depois de uma falha.

## Comportamento requerido

- Tokens de acesso e renovação devem ser cifrados antes de persistir. A aplicação continua trabalhando com texto claro em memória, sem expor tokens no Admin/API/logs. A migração cifra valores já existentes; não os apaga nem exige reconexão.
- A chave vem do segredo de aplicação fora do repositório. Se a chave não puder decifrar um token, a integração falha sem devolver o valor armazenado. Alterar o segredo requer migração controlada da chave ou nova autorização.
- Cada anúncio Shopee com sincronia ligada acompanha a versão de estoque local enviada com sucesso. O envio usa o saldo atual, inclusive na primeira ativação sem evento prévio.
- Uma falha em um anúncio não marca o evento como entregue para outro anúncio/conta. Na repetição, enviar a versão mais recente, jamais a quantidade histórica do evento.
- Eventos são encerrados quando todos os anúncios Shopee atualmente habilitados para o produto alcançaram aquela versão. Sem anúncio habilitado, o evento é ignorado e encerrado. Mercado Livre mantém seu envio manual separado.
- O marketplace não participa da transação de venda/compra; falha de rede não impede operação comercial.

## Aceite

Testes verificam criptografia e migração de dados, múltiplas contas Shopee, falha e repetição após evento mais recente, primeira sincronia, estado de cada evento e regressão Mercado Livre. Sem commit ou deploy nesta etapa.
