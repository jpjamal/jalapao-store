# Tarefas

- [x] `MarketplaceAccount` com token, expiração e a data de fim da autorização; migration.
- [x] Contrato `base.py` e registro de adaptadores por canal.
- [x] Assinatura da Shopee isolada e testada contra caso conhecido.
- [x] Cliente Shopee com transporte injetável, renovação de token e erro traduzido.
- [x] Serviços: conectar, renovar, importar anúncios casando por SKU, empurrar estoque.
- [x] API e tela de integrações: conectar, situação, vínculos e interruptor por anúncio.
- [x] Registro dos adaptadores no `ready()` do AppConfig, com teste de regressão.
- [x] Aviso de autorização perto de vencer, no painel, junto com o do certificado.
- [x] Testes sem rede cobrindo assinatura, tokens, casamento por SKU e o interruptor.
- [x] Publicação pelo GitHub — entrou em `d2dad37` e está em produção.
- [x] Primeira conexão real do Mercado Livre — conta 96417426 (ver spec 006).
- [ ] Primeira conexão real da Shopee. A hipótese do IP no retorno deixou de importar: o retorno
      agora é o domínio `jpsys.duckdns.org` (spec 008).
