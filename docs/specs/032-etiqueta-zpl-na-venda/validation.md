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

## Limites desta validação local

O mecanismo do Docker Desktop não respondeu e impediu a repetição da suíte no PostgreSQL 17. Foram feitas
tentativas de iniciar, consultar e reiniciar o mecanismo, sem acesso à API do Docker. O CI do projeto executará
essa suíte quando houver uma publicação autorizada.

O navegador automatizado do ambiente bloqueou endereços locais, portanto o fluxo visual não foi acionado por
ele. Nenhum ZPL real do dono foi usado para evitar copiar dados pessoais: a conferência final do OCR deve ser
feita com uma etiqueta real da Shopee. A API, o parser puro, o typecheck e o build cobrem o fluxo implementado,
mas não substituem essa conferência visual.

## Publicação

Ainda não há commit ou deploy desta spec.
