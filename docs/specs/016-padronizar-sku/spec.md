# 016 — Padronizar o SKU dos produtos antigos

Os produtos vindos do site anterior mantinham o código de lá (ex.: `p_mu33g2qt_gy1hi`); só os
cadastrados depois da spec 010 tinham o padrão `SKU-<iniciais>-<número>`. O dono pediu que todos
sigam o padrão.

## Comportamento
- A migração de dados `catalog/0005_padronizar_sku` roda no deploy e dá o código novo a cada
  produto fora do padrão, na ordem de cadastro, com a mesma regra do cadastro (iniciais sem
  acento e sem palavras de ligação, até 6 letras, e o número da sequência).
- Produto que já está no padrão não muda; rodar de novo não altera nada.

## Decisões
- **O código antigo não é guardado.** O sistema está em desenvolvimento e o dono dispensou o
  histórico. A migração não tem volta.
- **Vínculos com anúncios continuam:** `Listing` aponta para o produto, não para o código. Uma
  importação futura de anúncio que ainda traga o código antigo no Mercado Livre aparece como
  pendente, sem desfazer vínculo existente.
- A regra das iniciais é copiada dentro da migração (migração não depende de código do app); um
  teste compara as duas para avisar se divergirem.

## Validação
153 testes passando (3 novos em `apps/common/test_sku_padronizado.py`): código antigo vira
padrão, o novo não muda, códigos únicos, idempotente, regra igual à do cadastro.

Antes do deploy, 7 produtos na VPS com código antigo; só o DUMMY ARANHA com anúncio vinculado
(MLB7700023302, publicado pelo sistema, sem SKU enviado ao Mercado Livre).
