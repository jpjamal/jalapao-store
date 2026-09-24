# 011 — Validar o rascunho contra o Mercado Livre antes de publicar

Entrega 2 da [spec 009](../009-rascunhos-anuncios/spec.md). O rascunho continua podendo ser
salvo incompleto; esta mudança acrescenta uma ação explícita, **Validar no Mercado Livre**,
que diz exatamente o que falta para publicar — sem publicar.

## Comportamento

**Categoria.** O dono digita o título e pede sugestões: o Mercado Livre devolve até três
categorias prováveis a partir do título (`domain_discovery`), a primeira sendo a mais
provável. Escolher uma grava o `category_id` no rascunho. Continua sendo possível digitar o
código direto.

**Atributos da categoria.** Com a categoria escolhida, a tela mostra o formulário de
atributos daquela categoria, com os obrigatórios primeiro. Atributo de lista vira seleção
com os valores do Mercado Livre; número com unidade leva a unidade; texto é texto. Atributos
ocultos ou somente leitura não aparecem. O que for preenchido fica no rascunho.

**Validar.** A validação junta duas fontes e devolve um relatório único, separando **erros**
(impedem publicar) de **avisos** (não impedem, mas convém corrigir):

1. *Checagem local*, que não depende de rede:
   - título, preço e categoria preenchidos; título dentro do limite da categoria; preço acima
     do mínimo da categoria; categoria que aceita anúncio;
   - ao menos uma foto escolhida e não mais que o máximo da categoria;
   - fotos em JPG ou PNG — WebP não está entre os formatos aceitos pelo Mercado Livre;
     menores que 500×500 geram aviso (o Mercado Livre não amplia), abaixo de 1200×1200 geram
     recomendação;
   - atributos obrigatórios da categoria preenchidos;
   - estoque zero gera aviso: publicar exige pelo menos uma unidade.
2. *Simulação no Mercado Livre* — `POST /items/validate`, que confere o anúncio inteiro
   **sem criá-lo**. Cada causa devolvida entra no relatório com o tipo que o Mercado Livre
   deu (`error` ou `warning`).

**Nada é publicado.** Validar não cria anúncio, não envia foto, não mexe em estoque e não
cria `Listing`. Custo interno nunca vai no que é enviado.

## Decisões e limites

- **As fotos não vão na simulação.** Elas são privadas, e enviar ao Mercado Livre cria
  arquivos do lado de lá — isso é da publicação, entrega 3. A simulação vai sem fotos; a
  causa "fotos obrigatórias" que o Mercado Livre devolve por isso é retirada do relatório,
  porque as fotos já são conferidas pela checagem local.
- **Tipo de anúncio:** a simulação usa Clássico (`gold_special`). A escolha entre Clássico e
  Premium fica para a publicação.
- **Descrição** não entra na simulação — no Mercado Livre ela é enviada em chamada própria,
  depois de criado o anúncio. Descrição vazia gera aviso local.
- **Estoque zero:** a simulação envia 1 unidade para que as demais regras sejam conferidas;
  o relatório avisa que o estoque real é zero.
- Shopee fora desta mudança.

## Aceitação
Um rascunho sem categoria, sem preço e sem foto recebe os três erros sem chamar o Mercado
Livre para o anúncio. Um rascunho completo e válido resulta em "pode publicar" quando o
Mercado Livre responde 204. Uma causa `error` do Mercado Livre bloqueia; uma `warning`
não. Foto WebP é erro; foto de 400×400 é aviso. Atributo obrigatório vazio é erro e atributo
oculto nunca é exigido. Nenhuma chamada de criação (`POST /items`) acontece em momento algum.
Sem conta do Mercado Livre conectada, a resposta diz isso em vez de falhar.
