# Validação

## Em produção, primeira pesquisa real (25/09/2026, versão 97536ec)

- **Buscar produto** "carregador turbo 20w": 10 produtos do catálogo com nome, marca e modelo
  certos (Peining, Hrebos, Ugreen, Ecopower, Knup…). Preço vazio em todos.
- **Ofertas** de um deles: 404 "No winners found".
- **Mais vendidos** de "Celulares e Telefones": os 20, na ordem (Galaxy A17, Galaxy A07, Moto
  G06…), todos do tipo produto do catálogo. Preço vazio em todos.
- Pelo log, a resposta de `/products/{id}` traz `pdp_types: ["traditional"]`,
  `buy_box_winner: None`, `permalink: ""`, `family_name` e a foto em `pickers[].products[].thumbnail`.

Conclusão: a API entrega descoberta e ranking, não preço de concorrente. A tela foi revista
para isso.

## Automática (revisão)
136 testes passando; os de `apps/common/test_pesquisa_precos.py` usam o formato real acima:
- foto da variação do próprio produto em `pickers`; marca e modelo dos atributos;
- link: `permalink` quando existe, senão a busca do site pelo nome da família;
- nenhum preço é prometido na resposta;
- mais vendidos na ordem, completados por tipo, anúncios numa chamada só;
- só leitura; rotas exigem permissão, validam códigos antes de chamar o Mercado Livre, explicam
  a falta de conta; a rota de ofertas não existe mais.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## Em produção, versão a2e8712 (25/09/2026)
- Mais vendidos de "Celulares e Telefones": 20 itens, todos com foto e link para a busca do site
  pelo nome da família (ex.: `lista.mercadolivre.com.br/Samsung-Galaxy-A17`).
- Mais vendidos de MLB1000: a lista inteira falhou com "autorização recusada ou expirou". O log
  mostrou `GET /user-products/MLBU767944712 → 403 'caller is not allowed to access this user
  product'`: o Mercado Livre não libera detalhe de produto de outro vendedor. O token estava
  válido. Corrigido: item recusado fica na lista, na posição dele, como "Produto de outro
  vendedor (detalhes não liberados)", sem link; e 403 passou a ter mensagem própria, separada da
  de autorização vencida (401).
