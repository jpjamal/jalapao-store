# Validação em produção — 2026-09-24

- Aplicação criada no DevCenter com Authorization Code, Refresh Token e PKCE S256; retornos cadastrados para o IP e para `https://jalapao-store.217-216-82-25.sslip.io/jalapao-store/callback`.
- `ML_APP_ID` está em variável do GitHub Actions e `ML_CLIENT_SECRET` em Secret. O workflow #23 (`c8f4a72`) passou pelos testes, entregou o arquivo privado de ambiente à VPS e concluiu o deploy com os contêineres saudáveis.
- HTTPS na VPS: `/health`, `/jalapao-store/login` e `/jalapao-store/callback` responderam 200. A API de integrações sem autenticação respondeu 401, como esperado.
- O botão **Conectar Mercado Livre** gerou a URL de autorização com Client ID, retorno, `state`, `code_challenge` e método `S256`. Nenhum anúncio ou estoque foi alterado.
- A autorização parou antes da tela de consentimento: `auth.mercadolivre.com.br/authorization` respondeu 403 gerado pelo CloudFront quando o `redirect_uri` continha o IP da VPS. Uma requisição com o mesmo Client ID e um domínio de exemplo chegou ao servidor de autorização (HTTP 200), enquanto a variante com o IP respondeu 403. Isso indica bloqueio do retorno por IP no acesso à autorização, apesar de o DevCenter ter aceitado salvar o URI; não prova qual regra específica do Mercado Livre o bloqueia.

## Solução e conexão real

Foi escolhida uma opção gratuita para o teste: `jalapao-store.217-216-82-25.sslip.io`.
O DNS resolve para `217.216.82.25`, e a URL de autorização com esse host no
`redirect_uri` não recebeu o 403 do CloudFront na verificação sem `state`. O workflow
#24 (`63be453`) emitiu o certificado Let's Encrypt, válido até 2026-12-23, e concluiu
o deploy. `/health`, `/jalapao-store/login` e `/jalapao-store/callback` responderam 200
por HTTPS no novo host; o acesso por IP continuou respondendo 200.

O titular salvou o novo URI no DevCenter e se autenticou na loja pelo subdomínio. O botão
**Conectar Mercado Livre** abriu a tela de consentimento sem o 403, com Client ID,
`state` e PKCE S256. Após a autorização concedida pelo titular, o callback informou a
conta conectada e o painel **Integrações** mostrou uma conta Mercado Livre com token
válido. O ID da conta não é necessário para reproduzir o teste e não fica nesta nota.
Nenhum anúncio foi importado e nenhum estoque foi enviado.

## Próximo teste

Importar anúncios para conferir a leitura e os vínculos pendentes. Depois, testar o
envio manual de estoque apenas com anúncio de teste e saldo previamente conferido.
O `sslip.io` serviu ao primeiro teste. O envio manual de estoque continua reservado a
anúncio de teste com saldo previamente conferido.

## Migração para DuckDNS

O titular criou `jalapao-store.duckdns.org` e o registro A foi conferido apontando para
`217.216.82.25`. O commit `ce7b7a3` adicionou o endereço ao Nginx, à lista de origens
aceitas pelo frontend e backend e ao retorno padrão enviado pelo GitHub Actions. O
workflow #25 concluiu testes, build e deploy; o Certbot emitiu certificado para o novo
nome, com expiração informada em 2026-12-23. `/health`, `/jalapao-store/login` e
`/jalapao-store/callback` responderam 200 por HTTPS. O titular salvou o novo URI no
DevCenter e a URL pública de autorização do Mercado Livre respondeu 200, sem o bloqueio
anterior do CloudFront. O titular entrou na loja pelo DuckDNS, autorizou a conexão e o
painel exibiu a conta Mercado Livre com token válido. Nenhum anúncio foi importado e
nenhum estoque foi enviado. O endereço por IP continua disponível; o `sslip.io` será
retirado da configuração ativa depois dessa validação.

Referência oficial: [Autenticação e Autorização](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao).
