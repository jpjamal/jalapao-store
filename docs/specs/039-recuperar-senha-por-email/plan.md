# Plano

**Backend (`apps/accounts`, `apps/common`):**
- `PasswordReset` (migração 0002): usuário, `code_hash` único, `expires_at`, `used_at`, `invalidated_at`.
- `services.py`: `pedir`, `obter`, `redefinir` (transação com trava; valida a senha antes de gastar o link; bloqueia
  os `OutstandingToken` da pessoa; aviso por `transaction.on_commit`).
- `common/email.py`: `email_configurado`, `link_publico`, `enviar` (nunca levanta erro; endereço fora do log).
- `api/views.py` e `urls.py`: `auth/resources/`, `auth/forgot-password/` (escopo de limite `forgot`, 5/hora),
  `auth/reset-password/<código>/`; rotas públicas (`authentication_classes = []`, `AllowAny`).
- Configuração: `EMAIL_*` e `URL_PUBLICA` em `settings/base.py`; console em desenvolvimento e memória nos testes
  (`EMAIL_SEM_SMTP`).
- `definir_emails`: preenche o e-mail do `jpmorais` em branco a partir de `JPMORAIS_EMAIL`.

**Frontend:** a lista de rotas do BFF aceita `auth/resources`, `auth/forgot-password` e
`auth/reset-password/<64 hex>`; páginas `forgot-password-page.tsx` e `reset-password-page.tsx`; link e aviso no login.
O código do link é hexadecimal de propósito: o BFF só aceita segmentos `[-a-zA-Z0-9]`.

**Infra:** `docker-compose.deploy.yml` passa `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `URL_PUBLICA` e
`JPMORAIS_EMAIL`; o workflow escreve a senha de app em `.env.email` (600, só se o segredo existir, senão apaga o
arquivo); `infra/deploy.sh` lê `.env.email` e roda `definir_emails` depois das migrações.

**Ameaças tratadas:** enumeração de contas (resposta igual); força bruta e spam de e-mail (3/hora por conta, 5/hora
por IP); vazamento do banco (só hash do código); reutilização do link (uso único, 1 hora); sessão aberta após a troca
(refresh tokens bloqueados); segredo no repositório (e-mail e senha de app só em variável/segredo do GitHub).
