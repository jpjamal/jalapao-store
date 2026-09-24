# 007 — HTTPS no Traefik, não no Nginx

O Traefik já é o proxy da VPS: atende a porta 80 de todos os projetos e serve o Portainer.
O HTTPS, porém, ficou num Nginx exclusivo da loja, que segura a porta 443 sozinho. Esta
mudança passa o HTTPS para o Traefik também, para haver **um** ponto de entrada.

## Comportamento
- O Traefik passa a escutar em `websecure` (443) e a rotear a loja por HTTPS, tanto pelo
  domínio quanto pelo IP.
- O Nginx da loja deixa de publicar 443. Continua existindo como proxy interno, servindo a
  aplicação em HTTP na porta 8080 dentro da rede Docker, que é para onde o Traefik entrega.
- **Dois certificados, duas origens:**
  - `jalapao-store.duckdns.org` — emitido e renovado pelo **próprio Traefik**, via ACME
    HTTP-01 na porta 80, guardado em `acme.json`.
  - `217.216.82.25` — continua vindo do **Certbot da loja**, porque certificado de IP exige
    o perfil *shortlived* que o Traefik não emite. Entra no Traefik como certificado padrão
    (`tls.stores.default`), lido do volume de certificados compartilhado.
- O IP continua funcionando porque a Shopee ainda aponta para ele. Quando o retorno da
  Shopee migrar para o domínio, o Certbot pode sair de cena.
- O retorno OAuth da loja passa a ser o domínio.

## A virada é reversível e testável antes
O Traefik sobe primeiro publicando 443 **apenas em `127.0.0.1:8443`**, sem disputar a porta
com o Nginx. O deploy valida os dois certificados nessa porta e só então a porta pública é
trocada — por variável, não por edição de código.

## Não objetivos
- Não mexer no roteamento dos outros projetos que já usam o Traefik.
- Não migrar o certificado do IP para o Traefik: o perfil *shortlived* continua no Certbot.
- Não desligar o Certbot; ele segue renovando o IP.
- Não mudar nada da aplicação: só o caminho até ela.

## Aceitação
Com o Traefik na porta de pré-validação, `https://jalapao-store.duckdns.org:8443/health` e
`https://217.216.82.25:8443/health` respondem `ok` com certificado válido, enquanto o
público continua sendo servido pelo Nginx. Depois da virada, os mesmos endereços respondem
na 443 sem o Nginx TLS no ar, `http://` continua redirecionando com 308, e o Portainer e os
demais projetos seguem respondendo. Renovar o certificado do IP faz o Traefik reler a chave
sem reinício manual.
