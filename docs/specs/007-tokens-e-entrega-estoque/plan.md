# Plano técnico

Usar Fernet da biblioteca `cryptography` num campo Django `TextField` especializado. Derivar chave de 32 bytes do `DJANGO_SECRET_KEY` com separação de domínio estável; o segredo continua exclusivamente no ambiente do backend. A migração altera primeiro os campos para `TextField`, cifra dados legados e por fim muda o estado para o campo cifrado, tudo numa transação.

No estoque, persistir `Listing.last_pushed_version`. O botão Shopee percorre vínculos habilitados da conta; bloqueia cada vínculo, lê `Stock.quantity`/`version` no momento do envio, chama o adaptador e só então registra a versão. O outbox continua sendo criado na transação comercial e seu status é reconciliado para todas as contas Shopee após cada envio. O saldo local é a fonte da verdade. Mercado Livre segue com a rotina manual específica.
