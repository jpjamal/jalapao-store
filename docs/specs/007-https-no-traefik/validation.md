# Validação

Em 2026-09-24, **antes de publicar**. Nada foi aplicado no servidor.

## Conferido em máquina

- `docker compose config` passa nos dois projetos, `jalapao-store` e `traefikproxy`.
- `bash -n infra/deploy.sh` sem erro de sintaxe.
- **A detecção da porta 443**, exercitada nos três cenários que importam:

| Porta publicada pelo Traefik | Decisão | Certo? |
|---|---|---|
| `0.0.0.0 443` | assume o 443, Nginx TLS não sobe | sim |
| `127.0.0.1 8443` (pré-validação) | não assume, Nginx TLS continua | sim |
| nenhuma | não assume, Nginx TLS continua | sim |

  A lógica anterior, `grep '443->443'`, respondia **"assume"** no segundo caso — o que
  derrubaria o HTTPS durante a própria pré-validação. Testado e confirmado antes de trocar.

- A mesma checagem rodada **contra o servidor de verdade** devolve "não assume", que é o
  correto hoje: o Traefik publica só a porta 80.

## Um estrago meu, pego antes de publicar

Ao ajustar a validação no workflow do traefikproxy, uma substituição por intervalo de linhas
num arquivo com fim de linha CRLF **apagou metade do passo de deploy**: sumiram `set -e`, o
`cd`, a criação do `acme.json`, o `pull` e o `up` do Traefik — e o `EOF` que fecha o heredoc.
Publicado assim, o YAML quebraria; ou pior, se o heredoc fechasse por acaso, o deploy
validaria um Traefik que nunca foi recriado e daria por bom.

O passo foi reescrito inteiro de uma vez, em vez de mais cirurgia de linha, e conferido por
três lados: o YAML carrega num parser de verdade e tem os seis passos esperados; o script
que chega na VPS não tem nenhum `$` sem escape (que seria expandido vazio na máquina do
GitHub); e passa em `bash -n`.

## Estado do servidor no momento desta validação

- Nginx da loja (`jalapao-store-tls-1`) com a 443, saudável, servindo IP e domínio por SNI.
- `https://jalapao-store.duckdns.org/...` **valida sem `-k`** — o certificado do domínio já
  está correto e vale até 23/12.
- Traefik ainda na configuração antiga: porta 80 apenas, sem `acme.json`.
- Três certificados no Certbot: `jalapao-ip` (5 dias), `jalapao-duckdns` (89 dias) e
  `jalapao-domain` (89 dias) — este último é `jalapao-store.217-216-82-25.sslip.io`, sobra
  de uma primeira tentativa, sem nenhuma referência. Pode ser apagado.

## Limites da evidência

**Nada foi exercitado contra o Traefik com HTTPS ligado**, porque isso só acontece ao
publicar. Em especial continuam não verificados: a emissão do certificado do DuckDNS pelo
ACME do Traefik, o certificado do IP sendo servido como padrão a partir do volume
compartilhado, e o `--deploy-hook` do Certbot fazendo o Traefik reler a chave renovada.

O último é o que merece atenção depois da virada: a falha seria silenciosa — renovação
acontece, Traefik segue com a chave velha, e o sintoma só aparece quando o certificado
antigo vence. Vale conferir a data servida no 443 depois da primeira renovação do IP.

A Let's Encrypt limita **5 certificados por semana** para o mesmo conjunto de nomes; dois
já foram emitidos para o DuckDNS em 24/09. Se a virada precisar de várias tentativas, há
risco de esbarrar no limite — outro motivo para a pré-validação existir.

## A virada, em produção — 24/09/2026

**Primeira tentativa: falhou, e por erro meu.** O valor passado para `TRAEFIK_HTTPS_BIND` foi
`0.0.0.0`. O compose monta `"${TRAEFIK_HTTPS_BIND}:443"`, o que deu `0.0.0.0:443`, e o Docker
leu como *porta do host = 0.0.0.0*: `invalid hostPort: 0.0.0.0`. Eu só tinha validado o
compose com o valor padrão, nunca com o da virada. O valor certo é `0.0.0.0:443`.

O log do deploy mostrou que as travas fizeram o que deviam:

```
=== A 443 está com jalapao-store-tls-1; aguardando liberar (até 3 min) ===
=== HTTPS público: a 443 está livre, o Traefik vai assumir ===
=== Pulling images ===
invalid hostPort: 0.0.0.0
```

A trava esperou e viu a porta liberar; a falha veio no `pull`, **antes** de recriar o
Traefik. A porta 80, o Portainer e os outros projetos não foram tocados. Mas o Nginx já
tinha sido parado pelo vigia, e o HTTPS ficou fora por 3 a 4 minutos até ele ser religado.

**Segunda tentativa: funcionou.** Variável corrigida, Nginx TLS parado por SSH, deploy do
traefikproxy pelo *Run workflow*. Conferido no servidor e de fora:

- `traefikproxy-traefik-1` publica `0.0.0.0:443`; é o único container na 443.
- `jalapao-store-tls-1` parado.
- `jalapao-store.duckdns.org` recebe o certificado **emitido pelo próprio Traefik** (emissor
  YR2, até 23/12).
- `217.216.82.25` recebe o certificado **do Certbot**, servido como padrão a partir do volume
  compartilhado (emissor YE1, perfil shortlived, até 30/09).
- HTTPS 200 no IP, no domínio e no manual em PDF; `http://` segue redirecionando com 308.
- Portainer, Postgres e Redis intocados.

O `acme.json` passou por quatro recriações do Traefik sem reemitir certificado nenhum — o
arquivo seguiu com os mesmos 15994 bytes das 15:07. O limite semanal da Let's Encrypt não foi
gasto além da emissão inicial.

## O que continua sem prova

**A renovação do certificado de IP servida pelo Traefik.** O Certbot renova, o
`--deploy-hook` toca `/traefik-config/dynamic.yml`, e o Traefik deveria reler a chave. Nada
disso aconteceu ainda: o certificado atual vence em 30/09 e a renovação deve rodar por volta
de 28/09. Se o aviso não chegar ao Traefik, a renovação acontece em disco e o Traefik segue
servindo a chave velha até ela vencer. **Conferir a data servida na 443 depois de 28/09.**
