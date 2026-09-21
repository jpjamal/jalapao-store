# Pasta `dados/` (só no servidor)

A lista de produtos vive em `~/jalapao-store/dados/produtos.json` na VPS. Não está no
repositório de propósito: é dado, não código.

- `produtos.json` — a lista, gravada pela API a cada alteração
- `historico/` — as 30 últimas versões, uma por gravação; se algo for apagado por engano,
  a cópia anterior está aqui
- `senha.txt` — a senha que a API exige para gravar. Trocar a senha é editar este arquivo
  e reiniciar o container: `docker restart jalapao-api`

O `rsync --delete` do deploy ignora esta pasta, então publicar o site nunca mexe nos dados.
