# Validação

Em 29/09/2026, com a spec 022 já aplicada por cima:

- Suíte completa (187 testes) contra PostgreSQL 17 real, sem nenhum teste pulado: OK. Em
  SQLite, 187 testes com 5 pulados (concorrência): OK. `ruff`, `manage.py check`, contrato
  OpenAPI validado com `--fail-on-warn` e ausência de migrações pendentes: OK.
- Testes do GTIN: códigos válidos dos quatro tamanhos, dígito verificador errado, tamanho
  errado, letras, limpeza de espaços e hífens, vários produtos sem código, duplicidade,
  edição com o próprio código, apagar o código e busca pelo número.
- `tsc --noEmit` e `next build` sem erro.
- Na tela, com o app local: código com dígito inválido recusado com a mensagem do backend;
  código digitado com espaços e hífen gravado limpo; busca por Produtos encontrou pelo número;
  no campo de produto do Estoque, digitar o número e dar Enter escolheu o produto.

## Limites da evidência
Não foi testado com um leitor a laser físico: o Enter foi simulado pelo teclado, que é o
comportamento normal desses leitores. Nenhum GTIN é enviado a marketplace.
