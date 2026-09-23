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

## CI e produção — 2026-09-23
- [Deploy final de código 72ccd5b](https://github.com/jpjamal/jalapao-store/actions/runs/35897597437):
  todos os jobs passaram. HTTP respondeu308 para o mesmo caminho em HTTPS; proxies
  recriados para atualizar arquivos de configuração e resolução dos serviços.
- [Pipeline PostgreSQL / Docker / deploy](https://github.com/jpjamal/jalapao-store/actions/runs/35897454012):
  testes e builds passaram. Suite ampliada para 12 testes, incluindo duas disputas reais
  no PostgreSQL: última unidade e duas solicitações simultâneas com a mesma chave.
- OpenAPI gerado e validado sem warnings; Swagger acessado em produção após login no Admin.
- HTTPS externo validado sem ignorar certificados; certificado Let's Encrypt ECDSA para
  IP217.216.82.25, validade observada até 2026-09-30 08:40:23 UTC.
- Renovação `certbot renew --dry-run`: todas as renovações simuladas passaram.
- Login admin/jpmorais via BFF, cookie Secure e permissões totais confirmados; login real
  no Django Admin também confirmado no navegador.
- 7 produtos legados encontrados na API e na interface, quantidades0, sem vendas ou caixa
  fictícios na produção. Reimportações subsequentes preservaram os registros.
- Callback e três ferramentas HTTP200 por HTTPS; manual público preservado como PDF.
- API do catálogo sem autenticação respondeu401.
- Senha temporária fornecida pelo dono ausente dos arquivos publicáveis. Git autor/committer
  jpjamal <jpfisica3@gmail.com>, sem coautores.

## Limites da evidência
O teste de renovação usa staging e não espera seis dias para expiração real. O legado das
calculadoras foi preservado; a conversão OCR/Labelary depende do serviço externo e não foi
reexecutada com etiquetas pessoais. Não houve anúncio publicado nem sincronização Mercado Livre.
Backups de código/JSON/banco foram gerados; restauração completa em ambiente separado é futura.
