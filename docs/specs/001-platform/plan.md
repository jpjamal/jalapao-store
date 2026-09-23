# Plano técnico

Monólito modular Django: accounts, catalog, inventory, sales, finance, integrations.
Models ORM e migrations são infraestrutura/persistência; domain.py contém cálculo puro,
services.py casos de uso/transações, selectors.py consultas, api.py serialização/HTTP.
Não criar repositórios genéricos que apenas dupliquem o ORM. Relações FK PROTECT preservam
histórico. UUID nas entidades, unicidade e CheckConstraints no banco, Decimal para dinheiro.

Next.js App Router com Tailwind e componentes shadcn/ui versionados no projeto. BFF usa
cookies HttpOnly, SameSite e secure em produção para guardar JWT; navegador não grava tokens
em localStorage. API DRF valida permissões em toda operação. BFF valida origem nas mutações.

Docker multi-stage frontend; backend Gunicorn/WhiteNoise; PostgreSQL em volume próprio.
Proxy de entrada preserva prefixo, manuais públicos e challenge ACME. HTTPS por certificado
de IP de curta duração, com renovação automática e verificação real antes de declarar pronto.

Migração: preservar site/api legados no Git para rollback; ferramentas estáticas copiadas
para frontend/public/ferramentas, cadastro antigo encaminhado ao catálogo novo. JSON de produção
montado somente leitura no importador. Nunca estimar estoque de produtos antigos.

Testar domínio, permissões, integridade e idempotência, build TypeScript e integração PostgreSQL.
Registrar resultados reais em validation.md; marcar limitações, não transformar TODO em sucesso.
