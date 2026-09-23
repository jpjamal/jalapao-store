# Jalapão Store — orientação do projeto

O pedido de 2026-09-23 autoriza migração para Django/DRF/PostgreSQL e Next.js/Tailwind/shadcn.
Substitui as antigas restrições sem build, framework, banco ou login.

- Ler docs/constitution.md, docs/specs/001-platform e READMEs backend/frontend.
- Backend com uv, pyproject.toml, uv.lock e .venv; não Poetry nem Python global.
- Monólito modular por domínio. Serviços transacionais para estoque, vendas e caixa.
- Dinheiro Decimal, relações explícitas, migrations versionadas, permissões Django.
- Preservar paleta/tokens, ferramentas, produtos e manuais existentes.
- Taxas de marketplace não mudam sozinhas; distinguir estimativas de valores reais.
- Código na VPS somente pelo GitHub Actions. Não publicar app por SSH.
- Preservar dados/, manuais/, .env* e volumes em deploy e rollback.
- Job test placeholder preservado; testes reais estão no job quality.
- Autor exclusivo dos commits: jpjamal <jpfisica3@gmail.com>, sem coautores ou IA.
- Contexto original e segredos fora do Git. Admin/jpmorais não têm senha em código ou docs.
- Integração Mercado Livre ainda não ativada; não declarar sincronização concluída.
