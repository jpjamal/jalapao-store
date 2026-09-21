# Sistema Jalapão Store

Site interno da loja: HTML e JavaScript puro, sem build, sem framework, sem dependência
instalada. O que está em `site/` é o que vai para o ar em `/jalapao-store`.

## Regras da casa

- **Nada de build.** Se a solução exigir npm install, provavelmente não é a solução.
- **Cores só pelos tokens** do topo de `site/assets/jalapao.css`, que vêm da Paleta Jalapão
  (`Jalapao Midia/Paleta_Jalapao_design_system.html`). Nada de hex solto nas páginas.
- **A conta e o armazenamento ficam em módulos** (`site/assets/custo-3d.js`,
  `site/assets/produtos.js`), fora das telas.
- **Regra de negócio não muda sozinha.** Taxa de marketplace só muda com pedido explícito e
  conferida contra um pedido real do painel — ver `docs/calculadora-marketplace.md`.
- **O menu é repetido em cada página** (não existe include): mexeu em um, mexa em todos.
- **Commits com a identidade do dono da loja**, sem assinatura de assistente.

## Deploy

`push` na `main` → GitHub Actions → rsync + `docker compose up -d` no servidor.
Os manuais em PDF vão por SSH, fora do Git (`manuais/` é excluída do rsync).
