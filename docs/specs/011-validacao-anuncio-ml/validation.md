# Validação

Em 24/09/2026, no ambiente local e contra PostgreSQL 17 real.

## Testes — 104 no total, 22 desta mudança

Com o adaptador do Mercado Livre trocado por um falso que registra cada chamada:

- **Nenhuma chamada de criação.** Validar um rascunho completo faz exatamente três operações —
  categoria, atributos e `validate_item` — e nenhum `Listing` é criado.
- Rascunho vazio: erros de título, preço, categoria e foto, **sem chamar o Mercado Livre**.
- Rascunho completo com 204: "pode publicar". O envio leva `BRL`, o estoque real, marca e
  modelo como atributos, nenhuma foto — e **o custo interno (12,34) não aparece em lugar
  nenhum do envio**.
- Causa `error` do Mercado Livre bloqueia; `warning` não.
- Causa de foto (`item.listing_type_id.requiresPictures`) é retirada e contada.
- WebP é erro; 400×400 é aviso de "não amplia"; 800×900 é recomendação de 1200×1200; quatro
  fotos numa categoria de três é erro.
- Atributo obrigatório vazio é erro; obrigatório mas somente leitura, ou oculto, nunca é
  exigido.
- Título de 61 caracteres em categoria de 60 e preço abaixo do mínimo são erros.
- Estoque zero gera aviso, e a simulação vai com uma unidade.
- Sem conta do Mercado Livre: mensagem clara, na função e na API (400).
- Permissão: só leitura não valida (403); com alterar, valida (200).
- Busca com menos de 3 letras e código de categoria com `../` são recusados antes de qualquer
  chamada.

E o cliente real, com respostas gravadas no lugar do HTTP: 204 vira lista vazia; 400 devolve
as causas sem levantar erro; 400 sem causa vira erro de formato; 401 pede renovação; a
sugestão monta `/sites/MLB/domain_discovery/search?…&limit=3`.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.

## No navegador, ambiente local

- Dummy Aranha com rascunho vazio → **Salvar e validar**: "4 problemas impedem a publicação",
  com título, preço, categoria e foto; três avisos (condição, descrição, estoque zero); e a
  indicação de que só a checagem local rodou.
- **Sugerir pelo título** sem conta conectada: "Conecte uma conta do Mercado Livre em
  Integrações antes de validar."

## Limites da evidência

Na entrega local, **nada foi exercitado contra o Mercado Livre de verdade** — o ambiente local não tem conta
conectada. Os caminhos e formatos seguem a documentação oficial lida no dia, mas o que só a
resposta real confirma — os campos exatos de `settings` da categoria, se a causa de fotos
ausentes vem com o código esperado, as mensagens reais das causas — fica para o teste com o
rascunho do Dummy Aranha na VPS.

## Em produção, com a conta real (24/09/2026)

Rascunho do Dummy Aranha em https://jpsys.duckdns.org, categoria escolhida pela árvore do
Mercado Livre e atributos obrigatórios preenchidos, GTIN em branco.

1. Primeira simulação (35b179f + ed9042c): **1 erro** do Mercado Livre,
   `body.required_fields` — "The body does not contains some or none of the following
   properties [family_name]". A conta está no modelo "produto do vendedor" (User Products).
   Corrigido em 74c8708: a simulação reenvia com `family_name` e, se preciso, sem `title`.
2. Segunda simulação (74c8708): **"Pronto para publicar no Mercado Livre."** Sem erros. Avisos:
   - GTIN condicional — peça artesanal, sem código de barras; não bloqueia.
   - `User has not mode me1` — a conta não usa Mercado Envios 1. O envio não é mandado na
     simulação, então vale o frete configurado na conta. Fica para a entrega de publicação.

Nenhum anúncio foi criado: só `POST /items/validate`, `GET /categories/…` e
`GET /sites/MLB/…` foram chamados.

O que a resposta real confirmou e o que continua em aberto:
- confirmado: a causa vem com `code` e `message` no formato previsto; a árvore de categorias
  (`/sites/MLB/categories` e `children_categories`) funciona com o token da conta;
- em aberto: se esta conta recusa `title` quando manda `family_name` — a segunda simulação
  passou, mas o relatório não diz em qual das tentativas.
