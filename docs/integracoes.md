# Integrações com marketplace

A tela fica em **/jalapao-store/integracoes**. Shopee e Mercado Livre têm adaptadores
locais; a conexão real depende de credenciais próprias de cada plataforma.

## O que já faz

| Faz | Não faz |
|---|---|
| conectar a loja por autorização | criar ou editar anúncio |
| renovar o token sozinho | importar pedido e taxa real |
| espelhar os anúncios e vincular ao produto | empurrar preço |
| levar o saldo do estoque para o anúncio | campanha e Ads |

## Como se conecta

1. **Integrações → Conectar loja da Shopee.** O sistema monta um link assinado e leva você
   para a Shopee.
2. Você entra na conta da loja, confirma e escolhe por quanto tempo vale a autorização —
   o máximo é 365 dias.
3. A Shopee devolve para `/jalapao-store/callback` com `code` e `shop_id`. O código vale
   poucos minutos, então a página troca por token assim que abre. **Precisa estar logado
   na Jalapão Store nessa hora.**
4. A loja aparece na lista, com a data em que a autorização expira.

O `access_token` dura 4 horas e é renovado sozinho: antes de qualquer chamada, se faltar
menos de 10 minutos, renova. Se ainda assim a Shopee reclamar do token, renova e tenta mais
uma vez — e só uma, para não virar laço.

## Como os anúncios encontram os produtos

**Pelo código (SKU).** O sistema lê a lista de anúncios e procura um produto com o mesmo
código, ignorando maiúscula e espaço em volta.

- Achou: cria o vínculo, guarda título e saldo do anúncio para conferência.
- Não achou: o anúncio aparece na tela como **pendente**, e nada acontece.

**Importar nunca cria produto, nunca mexe em estoque e nunca mexe em custo.** Se um anúncio
ficou pendente, ou você cadastra o produto com aquele código, ou corrige o código do anúncio
no painel do marketplace — e importa de novo.

## Como o estoque é sincronizado

Cada vínculo tem um interruptor próprio, **desligado por padrão**. Isso é proposital: ligar
por engano num anúncio errado zera a oferta de um produto que estava vendendo.

Com ele ligado:

1. Qualquer mudança de saldo local — venda, compra, produção, ajuste — já grava uma intenção
   no `OutboxEvent`, **na mesma transação** que mexeu no estoque. Isso já existia antes da
   integração; ela só passou a consumir.
2. Para a Shopee, **Enviar estoque** lê o saldo atual de cada anúncio com sincronia ligada.
   Cada vínculo guarda a versão enviada. Para o Mercado Livre, o botão também lê o saldo
   atual, mas segue a rotina manual própria, sem consumir a fila da Shopee.
3. Um evento Shopee só é encerrado quando **todas as contas ativas** com anúncios
   habilitados daquele produto receberam uma versão ao menos tão nova quanto a do evento.
4. Se um anúncio falhar, a pendência continua e registra erro e tentativa. Ao repetir,
   vai o saldo **atual**, nunca a quantidade antiga do evento.

Duas garantias que valem entender:

- **O envio é só daqui para lá.** Saldo do marketplace nunca sobrescreve o seu. Se divergir,
  quem manda é o seu estoque.
- **Marketplace fora do ar não trava a loja.** O envio acontece fora da transação do
  estoque: uma venda baixa o saldo mesmo com a Shopee inacessível.

Evento sem anúncio Shopee habilitado é encerrado; se um vínculo for habilitado depois,
o próximo envio faz a primeira sincronia mesmo sem um evento novo. Contas desativadas
não bloqueiam a fila.

## Aviso antes de vencer

A autorização de uma loja vence calada: o token renova normalmente até o dia em que não
renova mais, e a sincronia simplesmente para. Por isso o **painel** avisa quando faltarem
15 dias ou menos, junto com o aviso do certificado. O limiar é `MARKETPLACE_ALERT_DAYS`.

Conta desativada e conta sem data de expiração não entram no aviso. Autorização já vencida
continua aparecendo — deixar de avisar justo quando quebrou seria o pior momento.

## Limites conhecidos

**Várias lojas Shopee.** Cada anúncio guarda a versão recebida. A primeira loja não
encerra um evento enquanto outra loja ativa tiver anúncio habilitado e atrasado.
Solicitações simultâneas para o mesmo anúncio são ordenadas por bloqueio no banco.

O Mercado Livre não tem esse problema porque não usa a fila: o envio dele lê o **saldo
atual** de cada anúncio com sincronia ligada, a pedido, e não consome nem marca nada da
fila da Shopee.

**O Mercado Livre recusa em vez de adivinhar.** Anúncio com variações, estoque Full,
depósito do vendedor ambíguo, `user_product_id` ausente numa conta com depósitos, ou
resposta sem `x-version` — em todos esses casos o envio falha com explicação e **não grava
nada** do lado de lá. É o comportamento certo para escrita de estoque: errar o depósito é
pior do que não enviar.

**Cada envio ao Mercado Livre custa chamadas extras.** Antes de gravar, o adaptador lê o
anúncio e o perfil do vendedor para decidir o modelo de estoque. Para algumas dezenas de
anúncios não pesa; se um dia pesar, o perfil dá para guardar por alguns minutos.

## Onde ficam os segredos

Em `.env.backend` no servidor, modo 600, **nunca no repositório**:

```
SHOPEE_PARTNER_ID=
SHOPEE_PARTNER_KEY=
SHOPEE_REDIRECT_URI=https://217.216.82.25/jalapao-store/callback
SHOPEE_API_BASE=https://openplatform.shopee.com.br
```

O `partner_key` não sai do backend: não vai para o front, não entra em log, e o admin do
Django esconde os tokens da conta.

Tokens de acesso e renovação e o verificador PKCE ficam cifrados no banco com Fernet.
A chave deriva do `DJANGO_SECRET_KEY`; **preserve esse segredo** no ambiente do servidor.
Alterá-lo sem reconectar as contas ou migrar a chave impede decifrar os tokens antigos.
A migração 0004 converte tokens já salvos; não coloca valores claros em logs.

`SHOPEE_API_BASE` é o domínio do Brasil. A Shopee separa por região, e escolher errado
responde *loja inexistente* — um erro que não parece erro de domínio.

### Sobre o redirect ser um IP

A Shopee exige que o domínio do `redirect_uri` bata com o declarado no Console dela. Hoje o
servidor só tem IP. **A documentação não diz que IP é proibido**, então a decisão do dono foi
tentar assim. Por isso o endereço é variável de ambiente: se recusar, muda a variável e um
registro no Console — não muda código.

## Mercado Livre

1. Configure `ML_APP_ID`, `ML_CLIENT_SECRET`, `ML_REDIRECT_URI` no backend. Configure
   `ML_PKCE_ENABLED=1` se a aplicação no DevCenter tiver PKCE habilitado. O URI de retorno
   deve coincidir exatamente com o cadastrado no DevCenter.
2. Em **Conectar Mercado Livre**, um usuário autorizado inicia o OAuth. O servidor guarda
   uma tentativa com `state` aleatório, vinculado ao usuário e válido por 10 minutos.
   A página de retorno troca `code` e `state` pelos tokens. O `user_id` vem do Mercado Livre.
3. **Importar anúncios** lê anúncios existentes. O vínculo por SKU começa desligado.
   Anúncios com variações ou SKU ambíguo ficam pendentes, sem mexer no estoque local.
4. **Enviar estoque** manda o saldo atual apenas aos vínculos ligados. Anúncio simples
   legado usa `/items/{id}`. Conta com `warehouse_management` usa User Products com
   `x-version`, somente quando há um único depósito do vendedor claramente identificado.
   Full, múltiplos depósitos e variações são recusados para evitar escrita errada.

Ainda não há publicação/edição de anúncios, pedidos, taxas, preço ou execução automática.
A importação por paginação comum limita-se a 1000 anúncios; acima disso é necessário
implementar `scan`. O botão de envio processa até 100 vínculos por chamada. A conexão real
e os fluxos remotos não foram validados sem uma aplicação e conta autorizadas.

O IP HTTPS no URI de retorno ainda depende de aceitação no DevCenter; isso não foi
confirmado localmente.

Especificação e critérios em [006-mercado-livre](specs/006-mercado-livre/spec.md).
Proteção dos tokens e entrega por anúncio em
[007-tokens-e-entrega-estoque](specs/007-tokens-e-entrega-estoque/spec.md).

## Onde isso vive

| O quê | Onde |
|---|---|
| Tela | `frontend/src/app/(store)/integracoes/page.tsx` |
| Retorno da autorização | `frontend/src/app/callback/page.tsx` |
| Contrato e registro | `backend/apps/integrations/base.py` |
| Assinatura da Shopee | `backend/apps/integrations/shopee/assinatura.py` |
| Adaptador da Shopee | `backend/apps/integrations/shopee/cliente.py` |
| Adaptador do Mercado Livre | `backend/apps/integrations/meli/cliente.py` |
| Casos de uso | `backend/apps/integrations/services.py` |
| Testes | `backend/apps/common/test_integracoes.py` |

Spec, plano e validação em [005-integracao-marketplaces](specs/005-integracao-marketplaces/spec.md).
