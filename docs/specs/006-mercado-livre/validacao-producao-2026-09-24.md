# Validação em produção — 2026-09-24

- Aplicação criada no DevCenter com Authorization Code, Refresh Token e PKCE S256; retorno cadastrado como `https://217.216.82.25/jalapao-store/callback`.
- `ML_APP_ID` está em variável do GitHub Actions e `ML_CLIENT_SECRET` em Secret. O workflow #23 (`c8f4a72`) passou pelos testes, entregou o arquivo privado de ambiente à VPS e concluiu o deploy com os contêineres saudáveis.
- HTTPS na VPS: `/health`, `/jalapao-store/login` e `/jalapao-store/callback` responderam 200. A API de integrações sem autenticação respondeu 401, como esperado.
- O botão **Conectar Mercado Livre** gerou a URL de autorização com Client ID, retorno, `state`, `code_challenge` e método `S256`. Nenhum anúncio ou estoque foi alterado.
- A autorização parou antes da tela de consentimento: `auth.mercadolivre.com.br/authorization` respondeu 403 gerado pelo CloudFront quando o `redirect_uri` continha o IP da VPS. Uma requisição com o mesmo Client ID e um domínio de exemplo chegou ao servidor de autorização (HTTP 200), enquanto a variante com o IP respondeu 403. Isso indica bloqueio do retorno por IP no acesso à autorização, apesar de o DevCenter ter aceitado salvar o URI; não prova qual regra específica do Mercado Livre o bloqueia.

## Próximo teste

Configurar um nome DNS para a VPS, emitir certificado HTTPS, atualizar o URI no DevCenter e no ambiente de produção e repetir a autorização. Só depois da conexão, testar importação em leitura e, por último, envio manual de estoque com anúncio de teste e saldo conferido.

Foi escolhida uma opção gratuita para o teste: `jalapao-store.217-216-82-25.sslip.io`.
O DNS resolve para `217.216.82.25`, e a URL de autorização com esse host no
`redirect_uri` não recebeu o 403 do CloudFront na verificação sem `state`. O workflow
#24 (`63be453`) emitiu o certificado Let's Encrypt, válido até 2026-12-23, e concluiu
o deploy. `/health`, `/jalapao-store/login` e `/jalapao-store/callback` responderam 200
por HTTPS no novo host; o acesso por IP continuou respondendo 200.

O novo URI está preenchido no formulário do DevCenter, mas ainda precisa ser salvo pelo
titular da conta após o aceite dos Termos e o reCAPTCHA. O OAuth completo permanece
pendente desse cadastro e de uma sessão autenticada no novo host (os cookies do acesso
por IP não são compartilhados com o subdomínio).

Referência oficial: [Autenticação e Autorização](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao).
