# Pasta `dados/` (só no servidor)

Resto do sistema anterior, mantido como **fonte de importação e rede de segurança**.
Não está no repositório de propósito: é dado, não código.

Desde 23/09/2026 o catálogo de verdade vive no PostgreSQL. Esta pasta continua no
servidor porque o `infra/deploy.sh` roda `import_legacy` a cada publicação, lendo
`produtos.json` montado no backend como `/legacy` em modo somente leitura. A importação
é idempotente: casa pelo `legacy_id`, não sobrescreve o que foi editado depois e não
inventa quantidade — estoque novo entra em zero.

- `produtos.json` — a lista como o sistema antigo deixou; não é mais escrita por ninguém
- `historico/` — as 30 últimas versões daquela época
- `senha.txt` — senha da API antiga, que não roda mais; sem efeito hoje

O `rsync --delete` do deploy ignora esta pasta, então publicar nunca mexe nos dados.
Cada importação também deixa uma cópia datada em `~/backups/jalapao-store/`.

Quando o catálogo no banco estiver consolidado e não houver mais o que reimportar, a pasta
pode sair — junto com o passo de importação no `deploy.sh`.
