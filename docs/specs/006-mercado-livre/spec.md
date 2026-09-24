# 006 — Mercado Livre

## Objetivo

Conectar a conta do vendedor pelo OAuth, importar anúncios existentes por SKU e permitir envio **manual e explícito** do saldo local aos anúncios vinculados. O estoque e o custo da Jalapão Store continuam sendo a fonte interna; a leitura remota nunca os altera.

## Regras

- Autorização iniciada por usuário autenticado com permissão de alterar integrações; `state` aleatório, vinculado ao usuário, expirado e consumido uma única vez. PKCE S256 configurável conforme a aplicação no DevCenter.
- A troca do código usa o URI de retorno fixo e o `user_id` devolvido pelo Mercado Livre; o cliente não escolhe o vendedor. Os tokens não saem da API.
- Refresh token é de uso único: serializar a renovação no banco, salvar o novo par e tentar novamente no máximo uma vez quando o acesso for recusado.
- Importação paginada, com SKU inequívoco. Sem SKU, SKU ambíguo ou variante com mapeamento ambíguo permanece pendente. Nenhum produto é criado; sincronia inicia desligada.
- Envio manual usa a quantidade **atual** do estoque local, nunca um evento antigo. Não consome nem marca entregue a fila da Shopee. Para contas multiorigem, somente um depósito do vendedor claramente identificado pode ser atualizado. Full, múltiplos depósitos, variações ou modo desconhecido falham sem escrita remota.
- Sem publicação de anúncios, preços, pedidos, notificações, execução automática ou conexão real sem credenciais nesta etapa.

## Aceite

Testes locais cobrem estado ausente/repetido/expirado, troca e refresh, importação segura e recusa de estoque em cenário ambíguo. A interface mostra conectar Mercado Livre, importar e enviar manualmente. Nenhum commit ou deploy faz parte desta entrega.
