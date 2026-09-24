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

**Nada foi exercitado contra o Mercado Livre de verdade.** O ambiente local não tem conta
conectada. Os caminhos e formatos seguem a documentação oficial lida no dia, mas o que só a
resposta real confirma — os campos exatos de `settings` da categoria, se a causa de fotos
ausentes vem com o código esperado, as mensagens reais das causas — fica para o teste com o
rascunho do Dummy Aranha na VPS.
