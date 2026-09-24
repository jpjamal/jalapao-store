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
As fotos privadas dos produtos ficam no volume `product_media`, separado do banco.
O deploy cria `media-<data>.tar.gz` na mesma pasta de backups após parar a API;
para restauração, recuperar o dump do banco e o arquivo de fotos da mesma data.

## HTTPS
Certbot 5.4 com webroot e perfil shortlived para o certificado por IP, que dura cerca de
seis dias. O endereço principal da loja é `https://jpsys.duckdns.org/jalapao-store`;
o acesso por IP permanece disponível. O `sslip.io` temporário foi retirado da
configuração ativa após a migração.
Certbot verifica renovação a cada 12h. Validar periodicamente os logs do certbot e a data
de expiração servida. Não foi contratado serviço adicional; o domínio é gratuito (DuckDNS).

### TLS no Traefik (spec 007, concluída em 24/09/2026)

O Traefik, que já era o proxy da VPS e serve o Portainer, termina o HTTPS: um ponto de
entrada só, para 80 e 443. O Nginx da loja deixou de ter porta pública e ficou como proxy
interno em HTTP na 8080. Além de servir o manual em PDF e o webroot do desafio ACME do
certificado de IP, ele encaminha as páginas Next.js, o Django Admin, os estáticos e a API.

Dois certificados, duas origens, e é assim de propósito:

| Nome | Emitido por | Validade | Por quê |
|---|---|---|---|
| `jpsys.duckdns.org` | Traefik, ACME HTTP-01 | 90 dias | o caminho normal |
| `217.216.82.25` | Certbot da loja, perfil *shortlived* | ~6 dias | certificado de IP exige esse perfil, que o Traefik não emite |

O do IP entra no Traefik como certificado padrão (`tls.stores.default`), lido do volume
compartilhado. Como o Traefik só relê certificado quando a configuração dinâmica muda, o
`--deploy-hook` do Certbot toca o `dynamic.yml` do traefikproxy — **por bind mount do
diretório, nunca do arquivo**: o rsync do outro deploy troca o inode, e um mount de arquivo
ficaria preso no antigo, deixando a renovação sem efeito e em silêncio. O `deploy.sh` recusa
rodar se a pasta vizinha `~/traefikproxy/traefik` não existir.

O backend já usa o retorno da Shopee no domínio atual, mas o cadastro no Console da
Shopee ainda precisa ser feito antes da primeira conexão. O acesso HTTPS por IP continua
disponível; só retirar seu certificado e o Certbot quando esse acesso deixar de ser necessário.

**A virada, em ordem.** Código e configuração só mudam por deploy. Por SSH, apenas parar ou
reiniciar container — nada que altere arquivo. Duas variáveis de repositório no GitHub
decidem quem termina TLS, e ambas começam no lado seguro:

| Variável | Repositório | Padrão | Na virada |
|---|---|---|---|
| `JALAPAO_TLS` | jalapao-store | `nginx` | `traefik` |
| `TRAEFIK_HTTPS_BIND` | traefikproxy | `127.0.0.1:8443` | `0.0.0.0:443` |

`TRAEFIK_HTTPS_BIND` precisa levar a porta junto: o compose monta `"${TRAEFIK_HTTPS_BIND}:443"`, e
`0.0.0.0` sozinho vira `0.0.0.0:443`, que o Docker lê como *porta do host = 0.0.0.0* —
`invalid hostPort`. Foi o que falhou na primeira tentativa da virada.

1. **Publicar a loja.** Cria o proxy HTTP na 8080 e as rotas HTTPS no Traefik. O Nginx
   continua na 443; nada muda para quem acessa.
2. **Publicar o traefikproxy.** Sobe o Traefik com a 443 só no loopback e valida os dois
   certificados por dentro. Nada muda para quem acessa.
3. **Trocar as duas variáveis** no GitHub.
4. **Parar o Nginx TLS por SSH:** `docker stop jalapao-store-tls-1`. A partir daqui o HTTPS
   está fora do ar — por isso o passo seguinte vem logo em seguida.
5. **Publicar o traefikproxy de novo.** Ele confere que a 443 está livre, assume e valida.
   Fim da janela de indisponibilidade.
6. **Publicar a loja de novo.** Com `JALAPAO_TLS=traefik`, remove o container do Nginx TLS
   e valida o HTTPS pelo Traefik.

Três travas protegem a sequência:

- **O Traefik recusa assumir a 443 se ela estiver ocupada**, e nesse caso nem é recriado.
  Isso importa porque ele é compartilhado: se subisse pedindo uma porta ocupada, falharia
  ao iniciar e derrubaria a porta 80 de todos os projetos, Portainer incluído.
- **A loja recusa `JALAPAO_TLS=nginx` com o Traefik já na 443**, em vez de tentar subir o
  Nginx numa porta ocupada no meio do deploy.
- **Quem publica a 443 é lido da porta de verdade**, não procurado no texto. `grep '443->443'`
  casaria com a pré-validação `127.0.0.1:8443->443/tcp` e desligaria o HTTPS por engano.

Voltar atrás é o inverso: as variáveis nos valores padrão, parar o Traefik não é
necessário — publicar o traefikproxy (volta ao loopback) e depois a loja (sobe o Nginx).

Depois da primeira renovação do certificado de IP, **conferir a data servida na 443**: se o
aviso ao Traefik falhar, a renovação acontece e ele segue com a chave velha — falha
silenciosa que só aparece quando o certificado antigo vence.

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
`docker compose -f docker-compose.deploy.yml --env-file .env.production --env-file .env.backend --env-file .env.marketplace`
seguido de `ps`, `logs --tail 100 backend`, `logs --tail 100 certbot`, etc. O perfil
`nginx-https` é apenas a reserva para retornar temporariamente ao Nginx na porta 443;
não deve ser usado na operação atual com `JALAPAO_TLS=traefik`.
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
