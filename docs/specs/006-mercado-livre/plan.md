# Plano técnico

Adicionar adaptador Mercado Livre isolado em `apps.integrations.meli`, com transporte HTTP injetável e respostas normalizadas. Guardar tentativa de OAuth no banco com hash do `state` e, se necessário, `code_verifier`; consumir sob bloqueio de linha. Reaproveitar conta e vínculo da integração atual, sem alterar o cliente Shopee. Usar uma rotina de envio manual específica do Mercado Livre para preservar o consumidor da fila existente. Registrar só um depósito `seller_warehouse` quando inequívoco; o restante retorna erro compreensível. O Next encaminha as ações pelo BFF autenticado.

Configuração local por variáveis: `ML_APP_ID`, `ML_CLIENT_SECRET`, `ML_REDIRECT_URI`, `ML_PKCE_ENABLED`. URI cadastrado no DevCenter deve ser idêntico ao configurado.
