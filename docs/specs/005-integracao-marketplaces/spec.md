# 005 — Integração com marketplaces (Shopee primeiro)

Uma camada de integração com marketplace, desenhada para dois: a Shopee agora, o Mercado
Livre depois. O que é comum aos dois vive na camada genérica; o que é específico vive no
adaptador de cada um.

## Comportamento

### Conta conectada
- O dono conecta a loja da Shopee autorizando o app: o sistema gera o link de autorização,
  a Shopee devolve `code` e `shop_id` no callback, e o sistema troca isso por
  `access_token` e `refresh_token`.
- O `access_token` da Shopee dura 4 horas. O sistema renova sozinho antes de expirar, e
  qualquer chamada que encontre o token vencido renova antes de tentar.
- A autorização da loja vale no máximo 365 dias. A data é guardada e o painel avisa quando
  estiver perto do fim, do mesmo jeito que avisa do certificado.
- Conectar, desconectar e reconectar são operações do dono, com permissão do Django.

### Catálogo espelhado
- O sistema importa a lista de anúncios da loja e guarda o vínculo entre o anúncio e o
  produto local (`Listing`). O casamento automático é por **código (SKU)**; o que não casar
  fica pendente para o dono vincular na mão.
- Um anúncio nunca cria produto sozinho. Importar anúncio não mexe em estoque nem em custo.

### Estoque empurrado
- Cada vínculo tem um interruptor próprio, **desligado por padrão**. Com ele ligado, toda
  mudança de saldo local gera intenção de sincronizar, e o envio leva o saldo para o
  anúncio correspondente.
- A intenção é gravada na mesma transação que mexeu no estoque, pelo `OutboxEvent` que já
  existe. Se o envio falhar, a intenção continua lá e é tentada de novo — o estoque local
  nunca depende do marketplace responder.
- O envio é sempre **daqui para lá**. Saldo do marketplace não sobrescreve o local.

## Não objetivos desta mudança
- **Não cria nem edita anúncio.** Publicar produto exige categoria, atributos obrigatórios,
  imagens e regras por categoria; é trabalho próprio, de outra spec.
- **Não importa pedido nem taxa real.** Pedido vira venda, venda mexe em dinheiro e baixa
  estoque: merece spec própria, com idempotência pela chave do pedido e tratamento de
  pedido cujo item não está vinculado.
- **Não empurra preço.** Preço é decisão comercial e o risco de errar é alto demais para
  entrar junto com o resto.
- **Não mexe em anúncio de Ads/campanha.** Pode nem estar liberado para o tipo de app.
- **Mercado Livre não é implementado aqui** — só a forma onde ele vai encaixar.

## Riscos aceitos, decididos pelo dono
- O `redirect_uri` aponta para o IP do servidor, sem domínio. A documentação da Shopee exige
  que o domínio do `redirect_uri` bata com o declarado no Console, mas **não diz que IP é
  proibido**. Vamos tentar com IP. Se recusar, o endereço é configuração — muda uma variável
  de ambiente, não código.
- O par `partner_id`/`partner_key` vive em variável de ambiente no servidor, nunca no
  repositório. Token e refresh token vivem no banco.

## Aceitação
Com credenciais configuradas, o sistema monta um link de autorização assinado e válido.
Voltando do callback com `code` e `shop_id`, guarda os tokens e mostra a loja conectada, com
a data em que a autorização expira. A importação de anúncios casa por SKU, deixa os demais
pendentes e não cria produto nenhum. Com o interruptor ligado num vínculo, mexer no estoque
local gera a intenção de sincronizar; com ele desligado, não gera. Uma chamada com token
vencido renova o token e refaz a chamada uma vez. Assinatura calculada conforme a
documentação, conferida contra caso conhecido.
