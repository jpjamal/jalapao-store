# Plano

Dois repositórios mudam, e a ordem entre eles importa.

## No `traefikproxy`
`traefik.yml` ganha o entrypoint `websecure` e o resolver ACME `duckdns` por HTTP-01 na
porta 80. `dynamic.yml` declara o certificado do IP como padrão da store TLS. O compose
monta `acme.json` (persistente, 600) e o volume de certificados da loja em somente leitura.

A porta HTTPS vem de `TRAEFIK_HTTPS_BIND`, com padrão `127.0.0.1:8443`. A virada é trocar
essa variável para `0.0.0.0` no GitHub e publicar — sem editar arquivo, e reversível pelo
mesmo caminho.

O workflow **descobre** a porta publicada pelo container e valida os dois certificados nela.
Validar uma porta fixa daria deploy por bom o que não foi testado.

## Na `jalapao-store`
`proxy.conf` novo: o gateway serve a aplicação em HTTP na 8080, que é o que o Traefik
consome. O `tls` (Nginx 443) vai para o perfil `nginx-https`, ligado só enquanto o Traefik
não tiver a 443. Os cabeçalhos `X-Forwarded-Proto` passam a sair de `$jalapao_forwarded_proto`,
fixado em `https` em cada server, porque atrás do Traefik o `$scheme` do Nginx é `http` e o
Django precisa saber que a ponta era TLS.

## Duas armadilhas que este plano evita
**Detectar a porta por texto.** `grep '443->443'` casa também com
`127.0.0.1:8443->443/tcp` — a loja desligaria o Nginx TLS enquanto o Traefik só escuta no
localhost, e o HTTPS cairia para todo mundo no meio da pré-validação. A checagem lê a porta
publicada e exige HostPort 443 fora do loopback.

**Bind mount de arquivo entre projetos.** O Certbot avisa o Traefik tocando o `dynamic.yml`,
porque o Traefik só relê certificado quando a configuração dinâmica muda. Montar o arquivo
não serve: o deploy do `traefikproxy` o reescreve por rsync, o inode muda e o mount fica
preso no antigo — a renovação passaria a não ter efeito, em silêncio. Monta-se o diretório.
O `deploy.sh` recusa rodar se a pasta vizinha não existir, porque a falha seria invisível.

## Ordem da virada

Regra do dono: código e configuração só por deploy; por SSH, só parar ou reiniciar.

Duas variáveis de repositório decidem, ambas começando no lado seguro: `JALAPAO_TLS`
(`nginx` → `traefik`) na loja e `TRAEFIK_HTTPS_BIND` (`127.0.0.1:8443` → `0.0.0.0`) no
traefikproxy. A decisão explícita substitui a adivinhação: a loja não deduz mais sozinha
quem deve segurar a 443, ela é informada, e confere a porta de verdade só para recusar uma
configuração inconsistente.

1. Publicar a loja — proxy na 8080 e rotas HTTPS. Nginx segue na 443.
2. Publicar o traefikproxy — 443 no loopback, valida os dois certificados.
3. Trocar as duas variáveis.
4. `docker stop jalapao-store-tls-1` por SSH. Começa a janela sem HTTPS.
5. Publicar o traefikproxy — confere a 443 livre, assume, valida. Fim da janela.
6. Publicar a loja — remove o container do Nginx TLS e valida pelo Traefik.

**O Traefik recusa a 443 ocupada antes de ser recriado.** É a trava mais importante: ele é
compartilhado, e recriado pedindo uma porta ocupada ele falharia ao iniciar e levaria junto
a porta 80 de todos os projetos e o Portainer.
