# Rascunho para teste de anúncio — Luminária Pimentão

Data: 2026-09-24. Estado: **validação tentada; anúncio não publicado**.

## Produto e conta

- Produto local: cadastro ainda nomeado `Luminaria Air FOrm`; SKU `p_mu5w9zrx_zx7pl`. O titular corrigiu o nome/modelo comercial para **Luminária Pimentão**.
- Nome comercial proposto: `Luminária Pimentão de Mesa USB Decorativa`.
- Conta Mercado Livre: `96417426`, site `MLB`, ativada no modelo User Products.
- Categoria sugerida pela API: `MLB1586 — Luminárias de Mesa` (permite anúncio).
- Estoque: o titular informou ter **1 unidade pronta**, mas o sistema ainda registra **0**. Não registrar entrada até confirmar o custo real e a operação.

## Proposta comercial para revisão

- Preço no Mercado Livre: **R$ 69,76**, confirmado pelo titular para envio ao validador.
- Custo local calculado: **R$ 34,88**, confirmado pelo titular para o rascunho; não foi registrada entrada de estoque.
- Tipo de anúncio: `gold_special` (Clássico).
- Taxa de venda estimada pela API para esse preço/categoria/tipo: **R$ 8,02**; não inclui outros custos de logística ou eventuais encargos aplicáveis.
- Quantidade inicial proposta: **1**, sujeita à conciliação do estoque local.
- Condição: novo. Marca Jalapão Store e modelo Pimentão, confirmados pelo titular para o validador.
- USB: sim. Motivo de GTIN vazio proposto: produto artesanal.
- A conta usa User Products: enviar `family_name`, deixar o Mercado Livre gerar `title` e incluir o SKU no atributo `SELLER_SKU`.

## Descrição proposta

Luminária Pimentão de mesa com base vermelha e difusor branco. O formato com gomos em relevo decora o ambiente mesmo quando a luz está apagada. O LED embutido produz luz suave de apoio para mesa de cabeceira, escrivaninha, estante ou sala.

Produzida em impressão 3D, com acabamento fosco e cuidadoso. Por ser artesanal, pode apresentar pequenas variações de textura e tonalidade.

Medidas aproximadas: 21 cm de altura e 15 cm de largura.

Conteúdo: 1 luminária (base vermelha e difusor branco), com LED e cabo USB.

Garantia legal para produto durável: 90 dias. Dúvidas sobre o produto podem ser enviadas pelo chat do Mercado Livre.

## Fotos candidatas

- Principal: `JALAPAO STORE/Produtos 3D/Luminarias/luminaria organica/photo_2026-08-12_10-24-54.jpg` — luminária acesa sobre mesa clara.
- Secundária: `JALAPAO STORE/Produtos 3D/Luminarias/luminaria organica/photo_2026-08-12_10-24-53.jpg` — luminária apagada, mostrando base e difusor.
- O titular confirmou que a pasta contém fotos da luminária. Ambas foram aceitas pelo serviço de imagens do Mercado Livre (HTTP 201), com IDs `783802-MLB118185579041_092026` e `773194-MLB118185460419_092026`. As cópias temporárias na VPS foram removidas; os originais locais permanecem.

## Resposta da API

- `POST /items/validate` com os dados e fotos aprovados: HTTP 400, código `shipping.lost_me1_by_user`, mensagem `User has not mode me1`.
- Uma segunda validação com `shipping.mode = me2` explícito retornou o mesmo erro.
- `GET /users/96417426/shipping_preferences` e `GET /sites/MLB/shipping_methods` inicialmente retornaram HTTP 403 com `PA_UNAUTHORIZED_RESULT_FROM_POLICIES`. A aplicação não tinha o escopo Vendas e envios. O titular autorizou adicionar **somente leitura**, salvou a alteração no DevCenter e reconectou a conta. A API confirmou o novo escopo `orders-shipments:/read-only`; a leitura das preferências passou a responder HTTP 200.
- Preferências atuais da conta: `me2` com `drop_off` ativo, além de `custom` e `not_specified`. A categoria `MLB1586` permite ME2 e não tem restrições (`restricted=false`). O simulador `POST /users/{user_id}/shipping_modes` respondeu HTTP 200 e ofereceu apenas `me2/drop_off` para o rascunho. `POST /categories/MLB1586/attributes/conditional` respondeu HTTP 200 sem outros atributos obrigatórios.
- Apesar disso, `POST /items/validate` continuou devolvendo `shipping.lost_me1_by_user` após a reconexão e com `shipping.mode=me2`, `site_id=MLB`, `channels=[marketplace]` e `free_methods=[]` explícitos. `seller_id` não é aceito no payload desse validador (`body.invalid_fields`), portanto foi removido da última chamada. O conflito entre o simulador de envio e o validador permanece sem resolução; **não presumir que a publicação funcionará**.
- O titular pediu para manter por enquanto a permissão de leitura de Vendas e envios, junto às permissões existentes, para continuar os testes futuros. Nenhuma outra permissão foi ativada.
- Nenhum `POST /items` foi executado. Não houve publicação, vínculo, alteração de estoque ou registro de entrada.

## Pendências antes do envio ao validador

1. Investigar com o suporte do Mercado Livre por que `/items/validate` exige `me1` embora a conta, a categoria e o simulador indiquem `me2/drop_off`. Não usar `POST /items` enquanto essa inconsistência não estiver esclarecida.
2. Informar peso e dimensões **embalado** para eventual configuração de envio.
3. Repetir a validação após resolver o bloqueio e revisar outros erros que a API possa revelar em seguida.

Após aprovação e validação, apresentar a resposta da API e o anúncio final para aprovação separada antes de publicar.
