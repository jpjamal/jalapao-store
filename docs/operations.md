# Operação, deploy e recuperação

## Publicação
GitHub main → workflow deploy.yml. Job test antigo preservado; job quality executa testes
Django em PostgreSQL real e build Next; job build valida e constrói imagens. Deploy rsync
preserva `.env*`, dados/, data/, manuais/ e não envia dependências locais.

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

infra/deploy.sh constrói, faz pg_dump quando há banco anterior, aplica migrations, interrompe
somente a API JSON antiga para importar uma cópia estável, sobe a stack e verifica HTTPS.
Backup JSON a cada importação; backup de código anterior no workflow. Arquivos sob
~/backups/jalapao-store com permissões restritas. Manuais públicos preservados em volume.

## HTTPS por IP
Certbot 5.4 com webroot e perfil shortlived; certificado de IP dura cerca de seis dias.
Traefik compartilhado mantém porta80, encaminhando somente rotas Jalapão e desafio ACME.
Nginx exclusivo usa443; não altera configurações dos outros projetos. Certbot verifica
renovação a cada12h; Nginx recarrega certificados a cada1h. Validar periodicamente logs de
certbot e data de expiração. Não foi contratado serviço adicional nem domínio.

Callback: `https://217.216.82.25/jalapao-store/callback`. Desde a spec 005 a rota é funcional:
recebe o retorno da autorização e troca o código por tokens — quem estiver logado vê a loja
conectada. O que ainda depende de cadastro e aprovação é a conta de desenvolvedor em cada
marketplace; sem credencial a rota não tem o que fazer.

O domínio do `redirect_uri` precisa bater com o declarado no Console do marketplace. Aqui ele
aponta para o IP, por decisão do dono: a documentação da Shopee não proíbe IP, e se o Console
recusar basta trocar `SHOPEE_REDIRECT_URI` e o registro lá — nenhuma linha de código.

## Comandos na VPS
Na pasta ~/jalapao-store, usar sempre:
`docker compose -f docker-compose.deploy.yml --env-file .env.production --env-file .env.backend --env-file .env.marketplace --profile https`
seguido de `ps`, `logs --tail 100 backend`, `logs --tail 100 certbot`, etc.
Se `.env.marketplace` ainda não existir, omita apenas essa opção; o script `infra/deploy.sh`
faz isso automaticamente.
Backup: `exec -T db pg_dump -U jalapao -d jalapao -Fc > backup.dump` em diretório privado.
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
