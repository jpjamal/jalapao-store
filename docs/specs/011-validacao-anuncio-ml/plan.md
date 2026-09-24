# Plano

## Fontes consultadas
Documentação oficial do Mercado Livre, lida em 24/09/2026: *Validador de publicações*
(`POST /items/validate`: 204 quando aceito, 400 com `cause` quando não, sem criar o anúncio),
*Validações* (estrutura de cada causa: `type` error/warning, `code`, `references`, `message`),
*Categorização de produtos* (`GET /sites/MLB/domain_discovery/search?q=&limit=`), *Atributos*
(`GET /categories/{id}/attributes`, com `tags`) e *Imagens* (JPG/PNG, até 10 MB, mínimo
500×500, recomendado 1200×1200, máximo por categoria em `max_pictures_per_item`).

## Onde cada coisa fica

| Onde | O quê |
|---|---|
| `integrations/meli/cliente.py` | `suggest_categories`, `category`, `category_attributes`, `validate_item` |
| `integrations/meli/anuncio.py` | regras puras (checagem local, montagem do envio, tradução das causas) e o orquestrador `diagnosticar` |
| `catalog/drafts_api.py` | `GET ml-categories`, `GET ml-attributes`, `POST {id}/validate` |
| `components/ml-anuncio.tsx` | escolha de categoria, formulário de atributos, relatório |

As regras ficam fora da view e fora do cliente HTTP: recebem dados já lidos e devolvem
achados. É o que permite testar cada regra sem rede.

## Decisões

**`tags` em dois formatos.** A documentação mostra as tags do atributo ora como objeto
(`{"required": true}`), ora como lista (`["required", "catalog_required"]`). `tags_de` aceita os
dois e devolve sempre um conjunto.

**O 400 da validação é resposta, não falha.** `validate_item` não usa o `_request` comum, que
transforma todo 4xx em exceção: aqui o corpo do 400 é justamente a lista de causas. 401, 403 e
429 continuam virando erro, e o 401 pede renovação de token pelo fluxo já existente.

**Simular só depois do básico.** Sem título, preço ou categoria, a simulação no Mercado Livre
só repetiria o que a checagem local já disse. Nesses casos ela não roda, e o relatório diz isso.

**Fotos fora da simulação.** Enviá-las criaria arquivos no Mercado Livre, o que é da
publicação. A simulação vai sem fotos; causas cujo código ou referência falam de `picture` são
retiradas e contadas, porque as fotos já foram conferidas localmente.

**Validar salva antes.** O botão "Salvar e validar" grava o rascunho e valida o que está
gravado — nunca o que só existe na tela.

**Permissão.** Consultar categoria e atributos pede leitura de rascunho. Validar é `POST`, mas
não cria nada: pede permissão de alterar rascunho, não de criar.
