# Operação, deploy e recuperação

## Publicação
GitHub main → workflow deploy.yml. Job test antigo preservado; job quality executa testes
Django em PostgreSQL real e build Next; job build valida e constrói imagens. Deploy rsync
preserva `.env*`, dados/, data/, manuais/ e não envia dependências locais. O que é a pasta
`dados/` do servidor e quando ela pode sair: [dados-LEIA-ME.md](../dados-LEIA-ME.md).

Pré-requisitos na VPS: `.env.backend` modo 600 com DJANGO_SECRET_KEY e POSTGRES_PASSWORD
aleatórios. `.env.production` continua sendo gerado pelo workflow. `.env.bootstrap` modo600
é opcional para criação inicial; remover após comprovar os logins, nunca versionar.
Nenhuma senha de usuário é colocada em configuração de imagem, argumento ou log.

As credenciais de marketplace moram no mesmo `.env.backend`, e nunca no repositório:
`SHOPEE_PARTNER_ID`, `SHOPEE_PARTNER_KEY`, `SHOPEE_REDIRECT_URI`, `SHOPEE_API_BASE`
(padrão `https://openplatform.shopee.com.br`, o domínio do Brasil) e, para o Mercado Livre,
`ML_APP_ID`, `ML_CLIENT_SECRET`, `ML_REDIRECT_URI` e `ML_PKCE_ENABLED`. Para o Mercado Livre,
o deploy também aceita `ML_APP_ID` como variável do GitHub Actions e `ML_CLIENT_SECRET` como
segredo do GitHub Actions. O workflow entrega esses valores em `.env.marketplace` na VPS,
com permissão 600; esse arquivo tem precedência sobre `.env.backend` e nunca entra no Git.
Sem as credenciais o sistema
sobe normalmente e a tela de Integrações responde qual variável falta — a integração é
opcional, não pré-requisito de deploy. `MARKETPLACE_ALERT_DAYS` ajusta com quantos dias de
antecedência o painel avisa que a autorização vai vencer; o padrão é 15.

Tokens e verificadores PKCE existentes são cifrados pela migração 0004 com chave derivada
de `DJANGO_SECRET_KEY`. Preserve esse valor no `.env.backend` entre versões e backups.
Trocar a chave sem migrar os tokens exige autorizar novamente as contas conectadas.
A migração 0004 não possui reversão automática para texto claro; para voltar a uma versão
anterior do código, restaurar o backup do banco feito antes dessa migração.

infra/deploy.sh constrói, para a API, faz pg_dump quando há banco anterior, aplica
migrations, leva as fotos e os manuais para o servidor de arquivos, interrompe somente a API
JSON antiga para importar uma cópia estável, sobe a stack e confere as rotas pelo Traefik
(front 200, admin 200, API sem rota pública, HTTP redirecionando para HTTPS, um manual 200).
Backup JSON a cada importação; backup de código anterior no workflow. Arquivos sob
~/backups/jalapao-store com permissões restritas.

## Arquivos: fotos e manuais (spec 020)

Ficam no **SILO**, o servidor de arquivos S3 do traefikproxy (fork AGPLv3 mantido do MinIO):

| Bucket | Conteúdo | Acesso |
|---|---|---|
| `jalapao-media` | fotos dos produtos | privado: saem pelo Django, com login |
| `jalapao-manuais` | manuais em PDF | público por objeto em `/manuais/<arquivo>`; listar não |

A chave da loja no SILO é gerada na VPS pelo deploy do traefikproxy, em
`~/traefikproxy/.env.silo.jalapao-store`, e o `deploy.sh` a entrega ao compose por
`--env-file`: nunca passa pelo GitHub. Sem `S3_ENDPOINT_URL` (desenvolvimento e testes), as
fotos ficam no disco, como antes.

- **Manual novo:** subir pelo painel do SILO (`https://jpsys.duckdns.org/silo`, bucket
  `jalapao-manuais`). A pasta `manuais/` da VPS ainda alimenta o bucket, mas só com o que
  falta: um PDF trocado pelo painel não é sobrescrito.
- **Migração:** o volume antigo `product_media` fica montado só para leitura em
  `/app/media-disco`; a cada deploy, `migrate_media_to_storage` copia o que ainda não está no
  bucket. Sai do compose depois de conferido em produção.
- **Backup:** `export_media` grava `media-<data>.tar.gz` lido do bucket, com a API parada, na
  mesma janela do dump do banco. Para restaurar, usar o dump e o arquivo de fotos da mesma data.

## Proxy e HTTPS (spec 019)

Um único proxy na VPS: o **Traefik central** do repositório `traefikproxy`, que também traz
o Portainer. A loja não tem Nginx nem Certbot: só declara as rotas dela em labels no
`docker-compose.deploy.yml`, e o Traefik as lê pelo Docker.

| Caminho | Vai para | Observação |
|---|---|---|
| `/jalapao-store/admin/`, `/jalapao-store/django-static/` | `jalapao-backend:8000` | única parte do backend na internet (Django Admin) |
| `/jalapao-store/callback` | `jalapao-frontend:3000` | `Referrer-Policy: no-referrer` (o código da autorização vai na URL) |
| `/jalapao-store` (resto) | `jalapao-frontend:3000` | cabeçalhos de segurança; envio limitado a 11 MB |
| `/manuais/<arquivo>` | SILO, bucket `jalapao-manuais` | leitura pública de objeto; listar não (spec 020) |
| `http://…/jalapao-store…`, `http://…/manuais/…` | redirecionamento 301 para HTTPS | middleware central `redirect-to-https@file` |

A API do Django **não tem rota pública**: o navegador fala só com o front, e o BFF do Next
chama `http://jalapao-backend:8000` pela rede interna do Docker. A documentação da API
(Swagger) fica para o ambiente local. Os serviços têm nomes únicos (`jalapao-db`,
`jalapao-backend`, `jalapao-frontend`) porque a rede `traefik_proxy` é compartilhada.

Certificados, ambos na infraestrutura central:

| Nome | Emitido por | Validade |
|---|---|---|
| `jpsys.duckdns.org` | o próprio Traefik (ACME HTTP-01, resolver `duckdns`) | 90 dias |
| `217.216.82.25` | o `certbot` do traefikproxy (perfil *shortlived*, modo standalone) | ~6 dias |

O Traefik ainda não emite certificado para IP (a correção está prevista para a v3.7), por
isso o Certbot continua existindo — mas centralizado. Ele renova a cada 12 h, avisa o Traefik
e deixa uma cópia pública do certificado no volume `infra_certificates`, que a loja monta só
para leitura: é de lá que o painel lê quantos dias faltam. O `deploy.sh` da loja recusa rodar
se a rede `traefik_proxy` ou esse volume não existirem — publique o traefikproxy antes.

A migração do Nginx para o Traefik e a história da 443 estão na spec 018; a retirada do Nginx
e do Certbot da loja, na spec 019.

Callback principal do Mercado Livre: `https://jpsys.duckdns.org/jalapao-store/callback`.
Desde a spec 005 a rota é funcional:
recebe o retorno da autorização e troca o código por tokens — quem estiver logado vê a loja
conectada. O que ainda depende de cadastro e aprovação é a conta de desenvolvedor em cada
marketplace; sem credencial a rota não tem o que fazer.

O `redirect_uri` precisa bater exatamente com o cadastrado no Console do marketplace.
O backend configura ambos os retornos para `https://jpsys.duckdns.org/jalapao-store/callback`.
O cadastro desse URI no DevCenter do Mercado Livre ainda não foi confirmado após a troca
de domínio. Para a Shopee, o URI ainda precisa ser cadastrado no Console antes do uso.

## Comandos na VPS
Na pasta ~/jalapao-store, usar:
`docker compose -f docker-compose.deploy.yml --env-file .env.production --env-file .env.backend --env-file ~/traefikproxy/.env.silo.jalapao-store --env-file .env.marketplace`
seguido de `ps`, `logs --tail 100 jalapao-backend`, `logs --tail 100 jalapao-frontend`, etc.
Logs do proxy e do certificado ficam no traefikproxy (`logs traefik`, `logs certbot`).
Se `.env.marketplace` ainda não existir, omita apenas essa opção; o script `infra/deploy.sh`
faz isso automaticamente.
Backup: `exec -T jalapao-db pg_dump -U jalapao -d jalapao -Fc > backup.dump` em diretório privado.
Restauração deve ser ensaiada em banco separado antes de substituir dados da produção.
Nunca executar `down -v` em produção.

## Rollback
Reverter commit no GitHub e publicar novamente; antes disso avaliar migrations incompatíveis.
Retorno ao legado JSON exige reconciliar vendas/movimentos registrados após o corte, pois
o JSON antigo não contém alterações do PostgreSQL. Não fazer rollback cego nem restaurar
snapshot sobre dados novos. Manter volumes PostgreSQL/certificados e backups mesmo em rollback.

## Limitações assumidas
Uma loja/uma moeda; sem fiscal ou integração automática ativa. Quantidades inteiras.
Financeiro é controle gerencial, não contabilidade. Custo corrente avalia estoque, lucro usa
snapshot por venda. Backup automático ocorre no deploy; agendamento diário e backup externo
são próxima tarefa operacional. Monitoramento externo de expiração ainda não configurado.
