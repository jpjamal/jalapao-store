# Constituição de desenvolvimento

1. Especificar comportamento e critérios antes da implementação; manter specs, contratos,
   testes e decisões coerentes no mesmo commit. Mudanças de escopo alteram a spec primeiro.
2. A autorização de 2026-09-23 substitui as antigas restrições sem framework/banco e acesso
   comercial aberto. Preservar identidade, regras de cálculo e dados reais.
3. Fonte da verdade comercial no backend. Dinheiro decimal; nenhuma baixa silenciosa ou
   edição destrutiva de histórico. Integração externa idempotente e auditável.
4. Nenhum segredo, dados pessoais de produção ou contexto com senha no repositório.
5. Publicação de código somente GitHub Actions. Preservar manuais/dados/backups no rsync.
6. Documentação SDD é instrumento vivo, não geração irrestrita. Uma pasta por mudança:
   spec.md → plan.md → tasks.md → validation.md. Dúvidas e não objetivos explícitos.
7. Commits com identidade jpjamal <jpfisica3@gmail.com>, sem atribuição de assistente.
