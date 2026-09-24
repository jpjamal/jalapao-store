# Validação

Em 2026-09-23.

## As contas não mudaram

Os módulos portados foram compilados e comparados, caso a caso, com o JavaScript original
de `site/`. Em todos, **todos os campos do resultado saíram idênticos** — não só o total:

| Caso | Custo | Preço |
|---|---|---|
| 45 g, 115/kg, 200 W, 5 h 18, kWh 1,56, margem 100% | 6,828600 | 13,657200 |
| 80 g, 115/kg, 200 W, 4 h 25, kWh 1,57, margem 100% | 10,586833 | 21,173667 |
| 150 g, 115/kg, 198 W, 14 h, kWh 1,67, mão de obra 13 | 34,879240 | 69,758480 |
| 12,5 g com vírgula decimal, 0 h 47, margem 60% | 8,715870 | 13,945392 |
| tudo em branco | 0 | 0 |

O mesmo cálculo no backend (`apps/catalog/domain.py`) devolve 6,83 / 13,66, 10,59 / 21,17 e
34,88 / 69,76 — os mesmos números com o arredondamento de centavos que só o backend aplica.
Tela e catálogo continuam concordando.

Faixas da Shopee conferidas nos dois lados de cada borda — 1, 8,99, 9, 20, 79,99, 80, 99,99,
100, 199,99, 200, 499,99, 500 e 1200 — com alíquota, taxa fixa e nome da faixa iguais. Venda
completa de R$ 79,99 com custo R$ 20 e recarga de 3%: taxas 20,4980, recarga 2,3997,
depósito 57,0923 e lucro 37,0923, iguais à conta original.

## Testes e build

- `ruff check`, `manage.py check`, `makemigrations --check` e `spectacular --validate
  --fail-on-warn` sem avisos, com o campo `certificate` já no contrato.
- Suíte contra PostgreSQL 17 real: **25 testes, todos passando**, incluindo os 4 de
  concorrência e os 3 novos do certificado.
- Certificado: um autoassinado de 30 dias não alerta; visto a 29 dias de distância, alerta.
  Caminho inexistente devolve `None` e o dashboard responde 200 do mesmo jeito.
- `npm run build`: TypeScript sem erro, com as rotas `/ferramentas/calculadora`,
  `/ferramentas/etiquetas` e `/ferramentas/impressao-3d` geradas.

## Em produção

Publicado por `614bf20` e, depois, `10f074f`. Conferido na VPS:

- Seis containers `healthy`; `/health`, `/jalapao-store/login`, `/jalapao-store/admin/` e
  `/manuais/dummy-13.pdf` respondendo como antes.
- As três ferramentas em `/jalapao-store/ferramentas/*` respondem 307 para quem não entrou,
  que é o esperado agora que estão atrás do login.
- Endereços antigos redirecionando com 308: `/calculadora.html` e
  `/ferramentas/calculadora.html` para `/ferramentas/calculadora`; `/produtos-3d.html` para
  `/produtos`.

**O aviso de certificado não funcionou de primeira.** O volume estava montado, mas o certbot
cria `live/` e `archive/` com permissão 0700 de root e o backend roda como usuário sem
privilégio: a leitura devolvia *Permission denied* e o aviso nunca apareceria. Afrouxar a
permissão não resolveria, porque o certbot reescreve os diretórios a cada renovação — então
o próprio laço do certbot passou a deixar uma cópia legível em `publico/cert.pem`. Depois
disso, lido do backend em produção:

```
{'expires_at': '2026-09-30T08:40:23+00:00', 'days_left': 6, 'alert': False}
```

Seis dias restantes e sem alerta, que é o estado saudável de um certificado shortlived.
A suíte passou a ter 27 testes com os dois novos casos dessa correção.

## Limites da evidência

O OCR não foi reexecutado com etiquetas reais nesta revisão: o código foi portado sem
alterar recortes, limiares nem regras de nome, mas quem confirma a leitura é uma etiqueta
de verdade. O mesmo vale para a renderização no Labelary, que depende de serviço externo.
O limiar do alerta foi exercitado com certificado autoassinado: em produção só se leu a
data real, sem forçar o caso de alerta — esse só aparece se uma renovação falhar de
verdade. Nenhuma transação de teste foi criada na VPS.
