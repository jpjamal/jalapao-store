# Gerador de etiquetas

Tela **Ferramentas → Etiquetas** (`/jalapao-store/ferramentas/etiquetas`) — o `.txt` de
ZPL que a Shopee gera vira um PDF por etiqueta, já com pedido, nome e cidade no nome do arquivo.

Até 23/09/2026 era a página `site/etiquetas.html`; virou tela do app com as mesmas regras
(spec 003). O código está em `frontend/src/features/tools/labels-page.tsx` e as regras de
OCR, fila e nome de arquivo em `frontend/src/features/tools/lib/etiquetas.ts`.

## O caminho do arquivo

1. Você solta o `.txt` (ou vários; também dá para colar o código).
2. A página manda o ZPL para a **API pública do Labelary**, que devolve a etiqueta
   desenhada em PNG — uma por vez, pelo índice.
3. Um OCR roda **no seu navegador** em cima desse PNG e compara mais de uma área para ler o destinatário.
4. Ao baixar, a página pede a mesma etiqueta em PDF e salva com o nome montado.

Na tela da ferramenta, o arquivo só sai do computador para o Labelary desenhar a etiqueta. Quando o ZPL
é adicionado a uma venda, ele também é salvo no servidor autenticado da loja para permitir a regeneração.

## Por que precisa de OCR

O ZPL da Shopee **não tem texto dentro**. A etiqueta inteira é uma imagem monocromática
compactada (`~DGR:DEMO.GRF` em Z64), desenhada com `^XGR`. Não existe nenhum campo `^FD`
para procurar: tentar ler o destinatário parseando o arquivo não funciona, a informação só
existe em pixel.

Cada etiqueta ainda vem com um segundo bloco `^XA ... ^IDR ... ^XZ` que só apaga o gráfico
da memória da impressora. O Labelary não conta esse bloco — o cabeçalho `X-Total-Count` traz
só as etiquetas de verdade.

## O que o OCR lê e como evita outro nome

O problema antigo vinha de um único recorte fixo: se o marketplace movesse o bloco, a primeira linha com
duas palavras podia ser do remetente ou de outra parte da etiqueta. Agora o navegador lê o recorte conhecido
e uma área maior. Se faltarem dados ou houver divergência, lê uma terceira área ampla.

As regiões da etiqueta renderizada a 8 dpmm são:

| Recorte | Área | Tratamento |
|---|---|---|
| Destinatário conhecido | x 0,02–0,575 · y 0,450–0,665 | ampliado 3×, binarizado |
| Destinatário ampliado | x 0–0,70 · y 0,390–0,760 | ampliado 3×, binarizado |
| Conferência ampla | x 0–1 · y 0,300–0,840 | usada quando as primeiras leituras divergem |
| Faixa do topo | x 0,02–0,99 · y 0,170–0,250 | ampliado 3×, binarizado |
| ID do pedido | x 0,025–0,36 · y 0,195–0,238 | ampliado 6×, **em cinza**, alfabeto travado em A–Z e 0–9 |

Binarizar o recorte do ID piora a leitura — por isso ele é o único em cinza.

Cada leitura produz um candidato com nome, cidade, estado e CEP. O parser usa os marcadores
**DESTINATÁRIO** e **REMETENTE**, reconhece CEP com ou sem hífen, cidade/UF na mesma linha e campos
rotulados. A melhor leitura precisa ser coerente; lacunas só são completadas por outra leitura com o mesmo
CEP. Endereços, entrega, frete e transportadora não podem virar nome. `O` ou `Q` no lugar de zero é aceito
somente na leitura numérica do CEP.

## Nome do arquivo

Oito padrões no seletor, sempre em minúsculas e sem acento:

| Padrão | Exemplo |
|---|---|
| Pedido + nome + cidade *(padrão)* | `2601010abcdefg_maria_de_souza_lima_palmas.pdf` |
| Pedido + nome + estado | `2601010abcdefg_maria_de_souza_lima_to.pdf` |
| Pedido + nome + cidade + estado | `2601010abcdefg_maria_de_souza_lima_palmas_to.pdf` |
| Pedido + primeiro e último nome + cidade | `2601010abcdefg_maria_lima_palmas.pdf` |
| Pedido + nome do destinatário | `2601010abcdefg_maria_de_souza_lima.pdf` |
| Só ID do pedido · pedido + rastreio · pedido + arquivo | conforme o caso |

O estado vira sigla por uma tabela dos 27 estados (a etiqueta imprime "Tocantins", o
arquivo sai `to`). Nomes repetidos ganham `_2`, `_3`. O campo é editável em cada cartão
antes de baixar, e trocar o padrão renomeia tudo de uma vez.

Se o OCR não achar o nome, o arquivo cai para `<nome do txt>_<número>`, e o cartão avisa
"não consegui ler o nome — digite".

## Etiqueta salva na venda

Em **Vendas → Nova venda**, a seção **Etiqueta ZPL**, no final do formulário, aceita `.txt` ou `.zpl` por
clique ou arrastando o arquivo para a área tracejada. O código bruto não fica editável. Depois da leitura,
só o número do pedido é aproveitado: ele vai para **Referência / número do pedido**, se ela ainda estiver
vazia (uma referência digitada à mão não é substituída), e é essa referência que fica gravada como pedido
da etiqueta. Destinatário, cidade e estado não aparecem, não são editáveis nem são guardados na venda; o
PDF baixado leva o número do pedido no nome.

No histórico de vendas, o ícone de etiqueta liga um ZPL a uma venda antiga ou abre o conteúdo
salvo e oferece **Baixar PDF** e **Abrir para imprimir**. Os dados corrigidos também ficam salvos, portanto a
regeneração mantém o mesmo nome de arquivo. A listagem não recebe o conteúdo ZPL; ele é buscado somente ao
abrir a venda específica. O limite por etiqueta salva é 5 MB.

## Tamanho da página do PDF

O seletor **Página do PDF** começa em **Do tamanho da etiqueta**: cada PDF tem só a etiqueta (4 × 6 pol,
102 × 152 mm), pronto para a impressora térmica. **A4** e **Carta** põem a etiqueta **centralizada**
numa folha comum, com o resto em branco — serve para imprimir em impressora de papel, mas não para a
térmica. O padrão voltou a ser o tamanho da etiqueta em 01/10/2026: na migração para o app ele tinha
ficado em A4 por engano, e os PDFs saíam numa folha inteira.

## Onde os PDFs caem

- **Botão "Escolher pasta de destino"**: salva direto na pasta escolhida. Funciona no
  Chrome e no Edge, inclusive com o arquivo aberto direto do disco.
- Sem escolher pasta, vão para a pasta de Downloads do navegador.
- **"PDF único (todas)"** junta todas as etiquetas do arquivo num PDF só.

## No celular

Abra a tela no navegador do celular, ou pelo app instalado (spec 014), com o mesmo login.
O botão de escolher pasta depende do navegador; sem ele, os PDFs vão para Downloads.

Para usar **sem login e sem o sistema**, existe a versão antiga num arquivo só,
`originais/etiquetas-arquivo-unico.html`: mande o arquivo para o celular (OneDrive, Drive ou
WhatsApp) e abra no Chrome. Ela não recebe as melhorias feitas no app.

## Configuração

Tamanho 100 × 150 mm e densidade 8 dpmm são o padrão da Shopee — **não mexa sem motivo**.
A densidade precisa ser a mesma em que a etiqueta foi desenhada; em 12 ou 24 dpmm a imagem
sai menor que o papel, porque a quantidade de pontos é a mesma num papel com mais pontos
por milímetro.

## Limites conhecidos

- O texto pequeno ou uma imagem ruim ainda pode trocar um caractere. Confira os campos mostrados; na venda,
  a referência pode ser corrigida antes de salvar.
- O OCR reconhece variações do layout Shopee/Correios. Etiqueta de outro marketplace continua virando PDF,
  mas pode exigir correção manual dos campos.
- **Precisa de internet**: o Labelary desenha a etiqueta e o motor de OCR é baixado do CDN
  na primeira leitura de cada sessão.
- **Limite gratuito do Labelary**: 3 requisições por segundo e 5.000 por dia. A página já
  enfileira com 360 ms entre chamadas e espera quando leva HTTP 429.
