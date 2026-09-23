# Evidências de validação

## Local — 2026-09-23
- uv.lock resolvido; backend/.venv isolado. Sem dependência Python global.
- Django system check: nenhum problema; migrations iniciais geradas.
- 11 testes descobertos: 10 passaram em SQLite, 1 concorrência adiado ao PostgreSQL do CI.
- Build Next.js e verificação TypeScript passaram.
- Navegador: login jpmorais, produto local R$10 custo/R$25 preço, entrada5 unidades;
  tentativa de venda6 rejeitada com mensagem da API; venda2 com desconto2/taxa3/frete5
  resultou bruto50/líquido40/lucro20; receber gerou caixa +40. Nada disso foi lançado na VPS.
- Fórmula 3D de referência: custo6,83 e preço13,66. Importação repetida preserva edições.

## Pendentes de evidência
CI PostgreSQL, imagens Docker, importação real, HTTPS, renovação e logins de produção.
Atualizar após observar resultados; não considerar testes locais equivalentes ao deploy.
