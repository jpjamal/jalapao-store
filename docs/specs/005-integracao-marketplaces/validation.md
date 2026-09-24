# Validação

> Registro da implementação inicial. A entrega de estoque e a proteção dos tokens foram
> revisadas depois na [spec 007](../007-tokens-e-entrega-estoque/validation.md).

Em 2026-09-23, ambiente local (`docker compose up`), banco PostgreSQL 17 e
`http://localhost:8080/jalapao-store`.

## O que foi provado sem rede

Toda a metade que é nossa está coberta por teste, com o transporte do cliente substituído
por uma função que devolve respostas gravadas.

**Assinatura.** A ordem da base string conferida nos dois formatos —
`partner_id + caminho + timestamp` para chamada pública e
`partner_id + caminho + timestamp + access_token + shop_id` para chamada de loja. O HMAC-SHA256
comparado com o cálculo feito à parte, 64 caracteres hexadecimais, e um teste que muda um
campo por vez para garantir que **qualquer** deles altera a assinatura.

**Ciclo do token.**

| Situação | O que acontece | Chamadas ao servidor |
|---|---|---|
| token vence em 2 minutos | renova antes de chamar | 2 |
| token aceito, servidor recusa com `error_auth` | renova e refaz | 3 |
| erro que não é de token (`error_param`) | erro sobe na hora | 1 |

A última linha é a que importa: erro comum não pode virar laço de renovação.

**Casamento por SKU.** ` 3d-ze-pilintra ` com espaço e caixa trocada acha
`3D-ZE-PILINTRA`. Anúncio sem correspondência fica pendente, **não cria produto** e não cria
vínculo. Reimportar atualiza o vínculo existente sem duplicar. Importar não mexe no estoque
local.

**O interruptor.** Desligado, o evento de estoque é encerrado sem enviar nada. Ligado, o
saldo vai e o vínculo guarda o valor e a hora. Envio que falha **não** encerra o evento:
guarda o erro, soma a tentativa e fica pendente para a próxima rodada.

**Permissões.** Sem permissão, nem lista nem conecta (403). Só com permissão de leitura,
lista mas não gera link de autorização. `connect` sem `code` responde 400 dizendo o campo
que falta. Erro de integração vira 400 legível, não 500.

**Aviso de autorização.** Longe do vencimento não aparece; dentro do limiar de 15 dias
aparece com os dias restantes; já vencida continua aparecendo; conta desativada e conta sem
data ficam de fora. O painel entrega o aviso junto com os indicadores.

Total: **66 testes** no backend, todos passando contra PostgreSQL real, com `ruff`,
`manage.py check`, `makemigrations --check` e o contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## O que foi conferido no navegador

Com credenciais **falsas** no ambiente local, a tela de Integrações gerou o link de
autorização e o sistema devolveu:

```
https://openplatform.shopee.com.br/api/v2/shop/auth_partner
  ?partner_id=1000001
  &timestamp=1790199450
  &sign=3b24af6be28117a60dbebfe9e8cf404fcf77058c951933613ad726cf9b5472f9
  &redirect=http%3A%2F%2Flocalhost%3A8080%2Fjalapao-store%2Fcallback
```

A assinatura foi recalculada por fora, com o mesmo par de chave e timestamp, e **bateu
exatamente**. Isso prova o caminho inteiro: tela → BFF → permissão → registro de adaptadores
→ credenciais → assinatura → resposta.

Sem credenciais, o mesmo botão responde *"Integração da Shopee sem credenciais: configure
SHOPEE_PARTNER_ID e SHOPEE_PARTNER_KEY no servidor"* — erro de configuração vira instrução,
não stacktrace.

## Um defeito que os testes não pegaram

A primeira versão respondia **"Canal sem integração disponível: shopee"** na tela, com a
suíte inteira verde. O decorador `@registrar` só roda quando alguém importa o pacote do
canal, e na aplicação rodando ninguém importava — nos testes, o próprio arquivo de teste
importava e mascarava o problema.

Corrigido com o `ready()` do AppConfig, que é o lugar certo para isso. O teste de regressão
que acompanha esvazia o registro, tira o módulo do cache de imports **e o atributo do pacote
pai** — sem isso o `from . import shopee` encontra o atributo antigo e nem tenta reimportar.

Vale registrar porque é a lição da rodada: teste verde não é prova de que a aplicação
rodando funciona, quando o teste importa algo que a aplicação não importa.

## Limites da evidência

**Nada foi exercitado contra a API real da Shopee.** Não há conta de desenvolvedor aprovada,
então tudo que depende do servidor deles responder está escrito conforme a documentação e
**não verificado**: nomes exatos de campo na resposta de `get_item_base_info` e
`get_item_list`, o formato de `update_stock` para item com e sem variação, os códigos de
erro de token, e o limite de chamadas por minuto. A primeira conexão real vai corrigir isso,
e é esperado que corrija.

**A hipótese do IP continua hipótese.** O link é montado com o IP no `redirect_uri` porque a
documentação não proíbe, mas quem decide é o Console da Shopee no momento do cadastro. Se
recusar, muda `SHOPEE_REDIRECT_URI` e o registro no Console — nenhuma linha de código.

**O que a spec não fez, e segue não fazendo:** publicar anúncio, importar pedido e taxa real,
empurrar preço, campanha e Ads.

Nada foi publicado na VPS. Nenhuma conta real foi conectada, nenhum anúncio lido, nenhum
estoque enviado a marketplace nenhum.
