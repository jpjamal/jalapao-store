# Gerador de etiquetas

`etiquetas.html` — o `.txt` de ZPL que a Shopee gera vira um PDF por etiqueta, já com o
nome do cliente no nome do arquivo.

## O caminho do arquivo

1. Você solta o `.txt` (ou vários; também dá para colar o código).
2. A página manda o ZPL para a **API pública do Labelary**, que devolve a etiqueta
   desenhada em PNG — uma por vez, pelo índice.
3. Um OCR roda **no seu navegador** em cima desse PNG e lê o destinatário.
4. Ao baixar, a página pede a mesma etiqueta em PDF e salva com o nome montado.

O arquivo do pedido só sai do computador para o Labelary desenhar a etiqueta. Nada é
enviado para servidor da loja.

## Por que precisa de OCR

O ZPL da Shopee **não tem texto dentro**. A etiqueta inteira é uma imagem monocromática
compactada (`~DGR:DEMO.GRF` em Z64), desenhada com `^XGR`. Não existe nenhum campo `^FD`
para procurar: tentar ler o destinatário parseando o arquivo não funciona, a informação só
existe em pixel.

Cada etiqueta ainda vem com um segundo bloco `^XA ... ^IDR ... ^XZ` que só apaga o gráfico
da memória da impressora. O Labelary não conta esse bloco — o cabeçalho `X-Total-Count` traz
só as etiquetas de verdade.

## O que o OCR lê

Três recortes da etiqueta renderizada a 8 dpmm, em fração da imagem:

| Recorte | Área | Tratamento |
|---|---|---|
| Bloco do destinatário | x 0,02–0,575 · y 0,450–0,665 | ampliado 3×, binarizado |
| Faixa do topo | x 0,02–0,99 · y 0,180–0,240 | ampliado 3×, binarizado |
| ID do pedido | x 0,04–0,30 · y 0,203–0,232 | ampliado 6×, **em cinza**, alfabeto travado em A–Z e 0–9 |

Binarizar o recorte do ID piora a leitura — por isso ele é o único em cinza.

Do bloco do destinatário saem nome, cidade, estado e CEP. O truque: **o CEP ancora tudo**.
A linha que casa com oito dígitos é o CEP; a de cima é a cidade e a de baixo é o estado.
O nome é a primeira linha com pelo menos duas palavras que não começa com "rua", "av",
"quadra" e afins.

## Nome do arquivo

Oito padrões no seletor, sempre em minúsculas e sem acento:

| Padrão | Exemplo |
|---|---|
| Nome + cidade *(padrão)* | `maria_de_souza_lima_palmas.pdf` |
| Nome + estado | `maria_de_souza_lima_to.pdf` |
| Nome + cidade + estado | `maria_de_souza_lima_palmas_to.pdf` |
| Primeiro e último nome + cidade | `maria_lima_palmas.pdf` |
| Só o nome do destinatário | `maria_de_souza_lima.pdf` |
| ID do pedido · Código de rastreio · Nome do arquivo + nº | conforme o caso |

O estado vira sigla por uma tabela dos 27 estados (a etiqueta imprime "Tocantins", o
arquivo sai `to`). Nomes repetidos ganham `_2`, `_3`. O campo é editável em cada cartão
antes de baixar, e trocar o padrão renomeia tudo de uma vez.

Se o OCR não achar o nome, o arquivo cai para `<nome do txt>_<número>`, e o cartão avisa
"não consegui ler o nome — digite".

## Onde os PDFs caem

- **Botão "Escolher pasta de destino"**: salva direto na pasta escolhida. Funciona no
  Chrome e no Edge, inclusive com o arquivo aberto direto do disco.
- Sem escolher pasta, vão para a pasta de Downloads do navegador.
- **"PDF único (todas)"** junta todas as etiquetas do arquivo num PDF só.

## No celular

O botão **Usar no celular** explica: copie a pasta `sistema jalapao store` inteira
(OneDrive, Drive ou cabo) e abra o `etiquetas.html` com o Chrome. A pasta precisa ir junto
por causa do estilo e do logo — se quiser mandar um arquivo só, use
`originais/etiquetas-arquivo-unico.html`, que é autossuficiente.

Se a página estiver sendo servida na rede local, o mesmo botão mostra um QR code do
endereço.

## Configuração

Tamanho 100 × 150 mm e densidade 8 dpmm são o padrão da Shopee — **não mexa sem motivo**.
A densidade precisa ser a mesma em que a etiqueta foi desenhada; em 12 ou 24 dpmm a imagem
sai menor que o papel, porque a quantidade de pontos é a mesma num papel com mais pontos
por milímetro.

## Limites conhecidos

- **O ID do pedido erra um caractere de vez em quando** (Q vira 0, J vira I). A fonte é
  pequena demais. Nome, cidade, CEP e código de rastreio saem exatos. Se for usar o ID como
  nome do arquivo, confira antes.
- **O OCR está calibrado para o layout Shopee/Correios.** Etiqueta de outro layout continua
  virando PDF normalmente, só o nome automático que não vai bater.
- **Precisa de internet**: o Labelary desenha a etiqueta e o motor de OCR é baixado do CDN
  na primeira leitura de cada sessão.
- **Limite gratuito do Labelary**: 3 requisições por segundo e 5.000 por dia. A página já
  enfileira com 360 ms entre chamadas e espera quando leva HTTP 429.
