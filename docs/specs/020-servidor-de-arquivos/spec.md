# 020 — Servidor de arquivos (SILO)

As fotos dos produtos moravam num volume Docker da loja (`product_media`) e os manuais em
PDF numa pasta da VPS servida pelo Nginx. Com o Nginx fora (spec 019) e a intenção de
centralizar a infraestrutura, os arquivos passam para um **servidor de arquivos S3
compatível** na infraestrutura central (traefikproxy), dividido com os outros sistemas.

## Escolha: SILO
Pesquisa de 28/09/2026, com a exigência do dono de licença copyleft (AGPLv3):

| Opção | Situação |
|---|---|
| MinIO | repositório **arquivado** em fevereiro de 2026; última versão em 15/10/2025; sem correções |
| **SILO** (`pgsty/silo`) | fork AGPLv3 mantido do MinIO; versões em 08, 09/2026; painel web completo |
| Garage | AGPLv3, independente e leve, mas sem painel web nem versionamento |
| SeaweedFS, RustFS | Apache 2.0 — fora pela licença |
| Nextcloud, Seafile | AGPLv3, mas são sincronizadores de pasta, não armazenamento S3 |
| Ceph | pesado demais para uma VPS |

O dono escolheu o SILO: mesmo formato e variáveis do MinIO, painel web para subir os manuais
pelo navegador. Risco aceito: mantido por equipe pequena, desde 02/2026. Se ele parar, o
Django não muda — qualquer servidor S3 serve, trocando só o endereço e a chave.

## Comportamento
- **Fotos dos produtos** no bucket **privado** `jalapao-media`. Continuam saindo só pelo
  Django, depois do login (`/api/v1/product-images/<id>/content`); o bucket não tem endereço
  público. Sem `S3_ENDPOINT_URL` (desenvolvimento e testes), continuam no disco.
- **Manuais** no bucket `jalapao-manuais`, com leitura **pública de objeto** e listagem
  proibida. O endereço não muda: `/manuais/<arquivo>` (o link do QR code do produto), agora
  roteado pelo Traefik direto para o SILO. O manual novo sobe pelo painel do SILO.
- Cada sistema tem um **usuário próprio no SILO**, que só enxerga os buckets dele. As chaves
  são geradas **na VPS** pelo deploy do traefikproxy e nunca passam pelo GitHub.
- **Migração sem perda:** o volume antigo fica montado só para leitura; o deploy copia para o
  bucket o que ainda não está lá (idempotente) e nunca apaga o disco. A pasta `manuais/` da VPS
  alimenta o bucket só com o que falta — um PDF trocado pelo painel não é sobrescrito.
  *(Feita e encerrada em 28/09/2026: volume e pasta apagados; o bucket é a única fonte.)*
- ~~Backup das fotos a cada deploy~~ — retirado a pedido do dono em 28/09/2026: sem backup
  de arquivos; só o dump do banco antes das migrations.

## Não objetivos
- Não servir foto por URL assinada nem pública: continua pelo Django, com login.
- Não apagar ainda o volume `product_media` nem a pasta `manuais/` da VPS: saem depois de a
  migração ser conferida em produção. *(Conferida e apagados no mesmo dia, 28/09/2026, a
  pedido do dono.)*

## Aceitação
Foto antiga visível depois da migração; foto nova grava no bucket e apaga dele; foto
inexistente dá 404; `/manuais/<arquivo>` 200 com `application/pdf` pelo domínio e pelo IP;
`/manuais/` sem listagem; bucket de fotos inacessível sem chave; a chave da loja não lê o
bucket do Vinculus.
