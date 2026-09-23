# Operação, deploy e recuperação

## Publicação
GitHub main → workflow deploy.yml. Job test antigo preservado; job quality executa testes
Django em PostgreSQL real e build Next; job build valida e constrói imagens. Deploy rsync
preserva `.env*`, dados/, data/, manuais/ e não envia dependências locais.

Pré-requisitos na VPS: `.env.backend` modo 600 com DJANGO_SECRET_KEY e POSTGRES_PASSWORD
aleatórios. `.env.production` continua sendo gerado pelo workflow. `.env.bootstrap` modo600
é opcional para criação inicial; remover após comprovar os logins, nunca versionar.
Nenhuma senha de usuário é colocada em configuração de imagem, argumento ou log.

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

Callback: `https://217.216.82.25/jalapao-store/callback`. App Mercado Livre ainda depende de
cadastro, permissões, credenciais e implementação OAuth; esta rota não confirma vinculação.

## Comandos na VPS
Na pasta ~/jalapao-store, usar sempre:
`docker compose -f docker-compose.deploy.yml --env-file .env.production --env-file .env.backend --profile https`
seguido de `ps`, `logs --tail 100 backend`, `logs --tail 100 certbot`, etc.
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
