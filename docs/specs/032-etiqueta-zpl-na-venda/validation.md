# Validação

## Automatizada

- Suíte completa com banco SQLite isolado: **330 testes aprovados**, 11 ignorados por dependerem de
  PostgreSQL ou serviços externos.
- Quatro casos específicos da etiqueta na venda: criação com ZPL, referência automática, conteúdo fora da
  listagem, leitura autenticada, rejeição de ZPL inválido, adição posterior, preservação de referência manual,
  campos corrigidos e permissão de alteração.
- Parser executado contra cinco disposições sintéticas: cidade acima do CEP, cidade/UF/CEP na mesma linha,
  campos rotulados, `O` no lugar de zero do CEP, estado acima do CEP e bloqueio de “Entrega padrão” como nome.
  O nome gerado foi `2601010abcdefg_joao_da_silva_palmas_to.pdf`.
- `makemigrations --check` sem alterações pendentes; Ruff aprovado.
- OpenAPI regenerado e validado sem avisos.
- Frontend: typecheck e build de produção aprovados, com as 20 rotas geradas.
- GitHub Actions executou a suíte completa no PostgreSQL 17, validou o backend e compilou o frontend
  novamente antes de liberar a imagem e o deploy.

## Limites desta validação local

O mecanismo do Docker Desktop local não respondeu. Essa limitação foi coberta pelo job obrigatório
**Django PostgreSQL and Next.js** do GitHub Actions, aprovado antes do deploy. Uma repetição local do build
também encontrou bloqueio `EPERM` do OneDrive na pasta temporária `.next`; o build limpo do CI foi aprovado.

O navegador automatizado do ambiente bloqueou endereços locais, portanto o fluxo visual não foi acionado por
ele. Nenhum ZPL real do dono foi usado para evitar copiar dados pessoais: a conferência final do OCR deve ser
feita com uma etiqueta real da Shopee. A API, o parser puro, o typecheck e o build cobrem o fluxo implementado,
mas não substituem essa conferência visual.

## Publicação

- Commit funcional: `9c28d3480a800e3686154d3f6e571a8db0dc378a`.
- Workflow **Deploy Jalapao Store** nº
  [38581591290](https://github.com/jpjamal/jalapao-store/actions/runs/38581591290): testes,
  PostgreSQL, frontend, imagem e deploy aprovados em 14/10/2026.
- Smoke público após o deploy: login e manifesto responderam `200`; `/vendas` redirecionou para o login;
  o BFF de vendas sem sessão respondeu `401`, preservando a proteção de acesso.
