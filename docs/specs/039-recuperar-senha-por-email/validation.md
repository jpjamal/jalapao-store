# Validação

## Automatizada (13/11/2026)

- `manage.py test apps.accounts`: 23 testes aprovados (pedido, resposta igual, limite por conta e por IP, SMTP
  fora do ar, link válido/vencido/usado, troca, outros links invalidados, sessões bloqueadas, aviso de senha
  alterada, senha fraca sem gastar o link, `definir_emails`).
- Suíte completa do backend: 353 testes, OK (6 ignorados, como antes).
- `makemigrations --check`: sem mudanças pendentes. `spectacular --validate --fail-on-warn`: aprovado; `docs/openapi.yml`
  regerado (só acréscimos). `ruff check`: aprovado.
- Frontend: `tsc --noEmit` e `npm run build` aprovados; rotas `/esqueci-senha` e `/redefinir-senha/[codigo]` no build.
- `docker compose config` resolve `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `URL_PUBLICA` e `JPMORAIS_EMAIL`;
  `bash -n infra/deploy.sh` sem erro.

## Teste de ponta a ponta local (banco descartável, e-mail no console)

- `definir_emails`: 1ª execução cadastrou o e-mail do `jpmorais`; 2ª, com outro endereço, preservou.
- Login mostrou "Esqueci minha senha"; o pedido respondeu a mensagem neutra; o e-mail saiu com assunto
  "Jalapão Store: criar uma senha nova" e o link `.../jalapao-store/redefinir-senha/<64 hex>`.
- A página do link mostrou a conta mascarada; `12345678` foi recusada ("muito comum", "inteiramente numérica") e o
  link continuou valendo; uma senha válida levou ao login com "Senha nova criada. Entre com ela."
- Depois: senha antiga → 401, senha nova → 200, o mesmo link → 410.

## Não conferido

- Produção: depende de o dono criar as variáveis/segredo no GitHub (ver a spec). A consulta ao banco da VPS para
  ver o e-mail atual dos usuários não foi feita (acesso por SSH negado nesta sessão); o `definir_emails` só preenche
  o que estiver em branco, então é seguro nos dois casos.
- O envio real pelo Gmail (SMTP) e o celular.
