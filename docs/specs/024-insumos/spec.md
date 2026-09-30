# 024 — Insumos: filamentos, embalagens, ferramentas e outros materiais

> **Situação: etapas 1 e 2 em produção (categorias e cadastro de insumos, filamentos multicolor,
> estoque em rolos, compras, pagamento e cancelamento); etapa 3 (insumos na venda) implementada
> localmente, com as decisões do dono abaixo.**
> Decisões já tomadas pelo dono: uma tela com duas abas; ferramentas só com nome e quantidade por
> enquanto; cancelamento de compra de insumo entra nesta spec; categorias de insumo cadastráveis.

## Objetivo

Insumo não é produto: não se vende, não tem preço de venda e não aparece em vendas nem em
anúncios. É o que a loja consome para fabricar, embalar, enviar ou operar, seja para peças 3D ou para produtos
de revenda (filamento, embalagem, etiquetas de impressora, fita, cola, verniz, lixa, ferramentas). Hoje o sistema só tem estoque de produtos, e o filamento é
digitado à mão, em R$/kg, em cada peça 3D.

Esta spec cria um cadastro **próprio** de insumos, organizado por **categorias de insumo
cadastráveis**, com estoque em unidades inteiras (para o filamento, **rolos inteiros**), compra
que gera saída no caixa ao ser paga (e pode ser cancelada), e a escolha dos filamentos no
cadastro da peça 3D. As peças são em geral **multicolor**: cada peça leva **uma ou mais linhas**,
uma por filamento, com as gramas usadas de cada um.

## Como o dono usa (telas)

Uma área nova, **Insumos**, no menu, com **uma tela e duas abas** (o saldo é uma coluna do próprio
cadastro, não há tela de estoque separada):

1. **Cadastro e estoque**: lista de insumos com categoria, saldo e, nos filamentos, o preço por
   grama e por kg. Ações por linha: Comprar, Dar baixa, Ajustar, Editar. Filtro por categoria e
   busca por nome ou cor. Um botão **Gerenciar categorias** abre o cadastro das categorias de
   insumo nesta mesma aba.
2. **Compras e movimentos**: histórico de compras (com Pagar e Cancelar) e de todas as
   movimentações de saldo, como no Estoque de produtos.

## Categorias de insumo

- Cadastráveis pelo dono, **separadas das categorias de produto** (spec 022): uma lista não
  aparece na outra, e uma categoria de insumo nunca serve para produto.
- Campos: nome (único, sem diferenciar maiúscula ou acento), `is_filament` ("esta categoria é de
  filamento") e ativa ou inativa. Não se apaga: desativa, e os insumos que já estão nela continuam.
- **Iniciais**, criadas pela migração (o dono pode renomear, acrescentar e desativar):

| Categoria | Exemplos |
|---|---|
| **Filamentos** (`is_filament`) | PLA preto, PETG transparente |
| **Embalagens** | caixas, sacos, plástico-bolha, etiquetas de envio |
| **Etiquetas e papelaria** | etiquetas térmicas, bobinas, papel, ribbon, tinta de impressora |
| **Colas e fitas** | cola instantânea, cola quente, fita dupla-face, durex |
| **Acabamento** | verniz, tinta, lixas, massa |
| **Ferramentas** | alicate, estilete, espátula, bico |
| **Outros** | o que não couber nas demais |

- Embalagem para peça 3D e embalagem para produto comum ficam na mesma categoria; se quiser
  distinguir, é pelo nome do insumo (ex.: "Caixa pequena – peças 3D"). Não há categoria por uso.
- `is_filament` **trava** depois que a categoria recebe o primeiro insumo, para nenhum insumo ficar
  sem os dados de filamento. A migração cria "Filamentos" com a opção ligada.

## Regras

**Cadastro de insumo**
- Todo insumo tem **categoria**, nome e unidade (texto, padrão "unidade"; por exemplo rolo,
  frasco, pacote, folha), mais observação opcional. O nome é único dentro da categoria.
- Insumo de categoria de filamento exige: material, cor, **peso do rolo em
  gramas** e **preço do rolo**. O **preço por grama** é `preço do rolo ÷ peso do rolo`
  (R$ 100,00 por 1.000 g = R$ 0,10 por grama) e o **preço por kg** é esse valor × 1.000. A tela
  mostra os dois. O sistema guarda o preço e o peso do rolo e **não arredonda o preço por grama**:
  só o total em centavos é arredondado. Os demais insumos não têm esses campos.
- **Material não é subcategoria**: as categorias não têm níveis. O material (PLA, PLA+, PETG, ABS, ASA,
  TPU e outros) é um campo do filamento, com sugestões prontas na tela para evitar variações de
  digitação ("pla" e "PLA"), e aceita outro valor digitado. A lista filtra por material e por cor.
  O material não entra na conta do custo.
- Insumo **não se apaga**: desativa (`active`). Inativo não aparece para escolher, mas o histórico e
  as peças ligadas a ele continuam.
- Insumo não tem SKU, preço de venda, GTIN nem categoria de produto, e nunca aparece em Vendas,
  Anúncios, Produtos ou no valor do estoque de produtos.
- Mudar um insumo de categoria só é permitido se a nova categoria tiver o mesmo `is_filament`.

**Estoque**
- Quantidade inteira (rolos, unidades), nunca negativa. Toda mudança de saldo passa por um
  serviço transacional único e grava um movimento (razão) com motivo, quem fez e saldo depois,
  no mesmo padrão do estoque de produtos.
- **Baixa** ("usei 1 rolo") e **ajuste** exigem motivo. Não há desconto automático por
  produção: quem controla o consumo é o dono, por rolo.
- Sem alerta de pouco estoque nesta versão.
- **Sem custo médio.** O estoque de insumos guarda só quantidade; não há valor de estoque de
  insumo. O custo que importa para o lucro vem do preço por grama dos filamentos escolhidos na peça.

**Compra de insumo**
- Registra insumo, quantidade, custo unitário (o preço do rolo, no caso do filamento), data,
  fornecedor e referência. Entra no saldo na hora.
- Fica "a pagar" até o dono clicar em **Pagar** e informar a data (não futura); pagar gera **uma**
  saída no caixa com o total, uma vez só, como a compra de produto. Compra cancelada não pode ser paga.
- Compra de filamento **atualiza o preço do rolo** do cadastro para o custo unitário da compra
  (o "último preço pago"); o dono pode editar o preço depois. A compra guarda o preço do rolo de
  antes (`previous_roll_price`).
- Chave de idempotência por compra, igual às entradas de produto.

**Cancelar compra de insumo** (mesmo modelo da spec 023; o registro não some)
- Botão **Cancelar** na compra, com confirmação. Só vale enquanto ela for a **última movimentação
  daquele insumo** (nenhuma baixa, ajuste, outra compra ou cancelamento depois dela); fora disso a
  API recusa com explicação, nada muda e a correção é pelo ajuste.
- O saldo perde a quantidade da compra. Compra já paga gera no caixa uma **entrada de estorno** com
  o mesmo valor, ligada à compra; compra não paga não mexe no caixa.
- Se a compra era de filamento e o preço do rolo ainda é o dela, o preço volta ao valor de antes
  da compra; se o dono já o editou, o preço atual é mantido.
- A compra fica com `status = cancelled` e `cancelled_at`; cancelar duas vezes não repete nada.

**Filamentos na peça 3D (multicolor)**
- O perfil de impressão 3D ganha **linhas de filamento**: cada linha é um filamento cadastrado e as
  **gramas** usadas dele na peça. Uma peça tem de 1 a 8 linhas, sem repetir o mesmo filamento, e as
  gramas de cada linha são maiores que zero. Só insumos de categoria de filamento entram aqui.
- **Custo do filamento da peça** = soma, linha a linha, de `gramas × preço por grama` do filamento,
  com o total arredondado em centavos. O peso total da peça é a soma das gramas das linhas.
- O preço de cada linha é **copiado** do filamento no momento em que a linha é salva, e não ligado
  ao vivo. Mudar o preço de um filamento **não muda** custo nem preço de nenhuma peça existente.
  A API e a tela só **avisam** "o preço do filamento X mudou" quando o valor guardado na linha
  difere do atual, e o dono atualiza se quiser.
- O restante do custo (energia, tempo, mão de obra, custos fixos e margem) **não muda**.
- Peça 3D **sem linhas** continua como hoje, com o preço por kg e o peso total digitados. Nenhuma
  peça existente é alterada.
- Filamento inativo não entra em linha nova, mas peças que já o usam continuam.
- A ferramenta **Custo de impressão 3D** usa a mesma conta, com as mesmas linhas, para dar o mesmo
  número da peça salva (hoje ela e o backend têm de bater).

**Permissões**: as do Django por modelo (ver, adicionar, alterar categoria de insumo e insumo;
adicionar e alterar compra de insumo; adicionar movimento), mais adicionar lançamento no caixa
para pagar e cancelar.

## Não objetivos (esta versão)

- Alerta de pouco estoque, desconto automático de filamento por produção, controle por gramas
  restantes e custo médio ou valor de estoque de insumos.
- Consumo de insumo ligado a cada venda ou a cada peça, ferramentas com controle de empréstimo,
  vida útil ou manutenção (só nome e quantidade), e importação dos cadastros antigos.
- Categoria de insumo por uso (peça 3D ou produto comum) e insumos compartilhados com produtos.
- Nas etapas 1 e 2 a baixa de insumo é sempre manual; a baixa junto com a venda é a etapa 3. Só o
  filamento se liga à peça 3D, pelas linhas de custo.

## Etapa 3 — insumos usados na venda

Decisões do dono (30/09/2026): avisar e dar baixa só do que tem; o custo do insumo **não** entra no
lucro; **sem** kit padrão por produto (os insumos são escolhidos na hora da venda); vendas importadas
do Mercado Livre **não** baixam insumo.

- **Registrar venda** ganha a seção opcional **Insumos usados**, **sempre visível**: sem insumos cadastrados ela
  orienta onde cadastrar, e se a lista falhar (ex.: sem permissão) mostra o motivo. Linhas: linhas com o insumo (a lista mostra o
  saldo) e a quantidade usada, por exemplo 1 caixa pequena e 2 etiquetas. Não se repete o mesmo
  insumo na venda, e a quantidade é maior que zero.
- Ao confirmar a venda, na **mesma transação**, cada insumo informado dá baixa no saldo, com a
  movimentação ligada à venda (`SupplyMovement.sale`, o vínculo que a etapa 2 já reservou).
- **Saldo insuficiente não impede a venda.** O insumo é baixado **só até onde tem** (nunca fica
  negativo) e a resposta da API e a tela avisam o que faltou ("pedido 5, baixado 3"). O pedido e o
  que foi de fato baixado ficam gravados na venda (`SaleSupply`: `requested` e `taken`), inclusive
  para o histórico.
- **Cancelar a venda devolve os insumos**: só o que foi de fato baixado (`taken`), mesmo que o
  insumo esteja inativo depois. Cancelar duas vezes não devolve duas vezes.
- Repetir o mesmo pedido de venda (mesma chave de idempotência) não baixa de novo.
- O **lucro da venda não muda**: o custo do insumo não entra nele (o estoque de insumo segue sem
  custo médio).
- **Vendas importadas do Mercado Livre não baixam insumo**: a baixa continua sendo manual.
- **Permissões:** informar insumos exige a permissão de movimentar o estoque de insumos; cancelar uma
  venda que baixou insumo também.
- A lista de vendas mostra os insumos usados de cada venda, e o que faltou quando for o caso.

Não objetivos da etapa 3: kit padrão por produto, custo de insumo no lucro, bloquear a venda por falta
de insumo, insumo nas vendas importadas e editar os insumos de uma venda depois de confirmada (cancela
e lança de novo).

## Validação

Testar categorias (criar, nome repetido sem diferenciar acento, desativar sem apagar, trava de
`is_filament`, as iniciais da migração), cadastro por categoria e cálculo do preço por grama e por
kg (inclusive rolo com preço que dá mais de duas casas por grama), unicidade por categoria, troca
de categoria com `is_filament` diferente recusada, saldo inteiro e nunca negativo, baixa e ajuste
com motivo, compra que entra no saldo e atualiza o preço do rolo, pagamento que gera uma só saída
no caixa, idempotência; cancelamento (restaura o saldo, estorno único no caixa se pago, volta o
preço do rolo só se não foi editado, recusa depois de outra movimentação, compra cancelada não é
paga, permissão); peça multicolor com custo somado por linha, igual no backend e na ferramenta,
sem arredondar o preço por grama; cópia do preço sem alterar peças existentes, aviso de preço
desatualizado, recusa de linha repetida, sem gramas, acima de 8 linhas, de filamento inativo ou de
insumo que não é filamento, peça sem linhas inalterada, permissões, migração sem mexer em produtos
e ausência de migrações pendentes.
