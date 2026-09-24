# Plano

## Onde cada coisa fica

```
apps/integrations/
├── models.py            MarketplaceAccount, Listing (já existia), OutboxEvent (já existia)
├── base.py              o contrato que todo marketplace cumpre + registro de adaptadores
├── shopee/
│   ├── assinatura.py    o cálculo do sign, puro e testável isolado
│   └── cliente.py       endereços, chamadas, tokens e erros da Shopee
├── services.py          casos de uso: conectar, renovar, importar anúncios, empurrar estoque
└── api.py               o que o painel consome
```

`base.py` é a costura pensada para o Mercado Livre. Um adaptador precisa saber responder:
montar link de autorização, trocar código por token, renovar token, listar anúncios e
atualizar estoque. Quem chama — os serviços — não sabe de qual marketplace se trata, só pede
o adaptador pelo nome do canal. O Mercado Livre entra como `apps/integrations/meli/` sem
tocar em serviço nenhum.

As diferenças já conhecidas entre os dois, que o contrato precisa aguentar: a Shopee assina
cada chamada com HMAC-SHA256 sobre `partner_id + caminho + timestamp + token + shop_id` e usa
token de 4 horas; o Mercado Livre usa OAuth2 com `Bearer` e token de 6 horas, sem assinatura
por chamada. Por isso o contrato fala em "preparar a requisição", e não em "devolver o
cabeçalho de autorização".

## Decisões

**Transporte injetável.** O cliente recebe a função que faz o HTTP. Em produção é `urllib`
da biblioteca padrão — o backend já não tem dependência de HTTP e não vale trazer uma por
isso. Nos testes é uma função falsa que devolve respostas gravadas. É o que permite testar
assinatura, renovação de token e tratamento de erro sem credencial nenhuma e sem rede.

**Renovação preguiçosa e antecipada.** O token é renovado quando falta menos de 10 minutos
para vencer, antes da chamada. Se ainda assim a Shopee responder erro de token, a chamada é
refeita **uma vez** após renovar. Duas tentativas no máximo, para não entrar em laço.

**Estoque pelo outbox que já existe.** `adjust_stock` já grava `OutboxEvent` com tópico
`inventory.changed` em toda alteração — a integração passa a ter um consumidor para isso, em
vez de inventar outro caminho. Envio fora da transação do estoque: marketplace fora do ar não
pode impedir de dar baixa numa venda.

**Segredo só no ambiente.** `SHOPEE_PARTNER_ID`, `SHOPEE_PARTNER_KEY`, `SHOPEE_REDIRECT_URI`
e `SHOPEE_API_BASE` em `.env.backend` no servidor. O `partner_key` nunca sai do backend, nem
para o front, nem para log.

## O que fica pendente por não dar para conferir daqui
Sem conta de desenvolvedor aprovada não há como bater contra a API real. Tudo o que depende
do comportamento do servidor da Shopee — nomes exatos de campo na resposta, códigos de erro,
limite de chamadas — fica escrito conforme a documentação e marcado como não verificado na
validação. O que dá para provar sem rede está coberto por teste.
