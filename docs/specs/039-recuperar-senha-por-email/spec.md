# 039 — Recuperar a senha por e-mail

Pedido do dono (13/11/2026): esqueceu a senha da Jalapão Store. Pediu para ver como o **Vinculus** (spec 070)
e o **Controle de gastos** (spec 003) fazem a recuperação, copiar o modelo e garantir que o usuário `jpmorais`
tenha o e-mail `jpmoraisc@gmail.com` cadastrado.

## Hoje (antes desta spec)

- Login só por usuário e senha; não existia recuperação.
- `bootstrap_users` cria `admin` e `jpmorais` **sem e-mail**.
- Não havia nenhuma configuração de e-mail no backend nem no deploy.

## Como os outros projetos fazem

- **Vinculus (070):** "Esqueci minha senha" no login; resposta sempre igual exista ou não a conta; link de
  1 hora e uso único (banco guarda só o hash); no máximo 3 pedidos por hora por e-mail; trocar a senha encerra as
  sessões e avisa por e-mail; SMTP do Django com Gmail (senha de app); sem e-mail configurado a opção some.
- **Controle de gastos (003):** mesma ideia, com o token do Django e limite por IP; Mailpit em desenvolvimento.

A Jalapão segue o modelo do Vinculus.

## Comportamento

- **Login:** mostra "Esqueci minha senha" só quando o envio de e-mail está ligado (`GET /auth/resources/`).
- **Pedido** (`/esqueci-senha`): a pessoa informa o e-mail; a resposta é sempre "Se esse e-mail tiver conta,
  enviamos um link." Só com conta **ativa** com aquele e-mail (sem diferença de maiúscula), envio ligado e menos de
  3 pedidos na última hora sai o e-mail. Além disso, 5 pedidos por hora por IP (429 acima disso).
- **Link** (`/redefinir-senha/<código>`): código aleatório de 64 caracteres hexadecimais, **1 hora**, **uso único**;
  o banco guarda o SHA-256. Vencido, usado, invalidado ou inexistente → 410 "Este link não está mais disponível".
  A página mostra a conta com o e-mail mascarado (`jp***@gmail.com`).
- **Senha nova:** com confirmação e as validações do Django (mínimo 8, não comum, não só números, não parecida com o
  usuário). Senha recusada **não gasta** o link. Ao trocar: usa o link, invalida os outros links da pessoa, coloca
  os refresh tokens dela na lista de bloqueados (as sessões não renovam) e manda e-mail "sua senha foi alterada".
  O token de acesso já emitido vale até o fim dos 15 minutos.
- **E-mail do `jpmorais`:** o comando `definir_emails` (roda no deploy) preenche o e-mail do `jpmorais` **só se
  estiver em branco**, lendo a variável `JPMORAIS_EMAIL`. O endereço fica numa variável do GitHub, não no
  repositório (público). O `admin` não recebe e-mail.

## Para funcionar em produção (feito pelo dono, no GitHub)

| Onde | Nome | Valor |
|---|---|---|
| Variável | `EMAIL_HOST_USER` | a conta Gmail que envia |
| Segredo | `EMAIL_HOST_PASSWORD` | senha de app dessa conta Gmail |
| Variável | `JPMORAIS_EMAIL` | `jpmoraisc@gmail.com` |

Sem `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`, tudo funciona como antes e o link "Esqueci minha senha" não aparece.

## Fora do escopo

Troca de senha com a pessoa logada; e-mails em HTML; provedor transacional e domínio próprio; limite de pedidos
compartilhado entre processos (o limite por IP usa o cache do processo, como o do login).

## Aceitação

- **039-C1** `GET /auth/resources/` diz se o envio está ligado.
- **039-C2** `POST /auth/forgot-password/` responde sempre 202 com a mesma mensagem; só conta ativa com e-mail
  recebe o link; quarto pedido na hora não envia; e-mail inválido → 400; sem envio ligado nada sai.
- **039-C3** `GET /auth/reset-password/<código>/` → 200 com e-mail mascarado ou 410.
- **039-C4** `POST` troca a senha, usa o link, invalida os outros, bloqueia os refresh tokens e avisa por e-mail;
  senha fraca ou confirmação diferente → 400 sem gastar o link; link usado → 410.
- **039-C5** Login com a senha antiga falha e com a nova entra.
- **039-C6** `definir_emails` preenche só o `jpmorais` em branco, preserva e-mail existente e ignora variável
  ausente ou inválida.
- **039-C7** Telas: link no login (só com envio ligado), `/esqueci-senha`, `/redefinir-senha/<código>` e aviso
  "Senha nova criada" no login.
