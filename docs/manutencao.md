# Manutenção

Como o projeto é montado e onde mexer.

## Estrutura

```
sistema jalapao store/
├── index.html            hub com as ferramentas
├── impressao-3d.html     custo da peça impressa
├── produtos-3d.html      lista das peças salvas
├── calculadora.html      lucro no marketplace
├── etiquetas.html        ZPL → PDF
├── LEIA-ME.md
├── assets/
│   ├── jalapao.css       tokens + componentes, usado por todas as páginas
│   ├── custo-3d.js       a conta do custo de impressão, sem tocar em tela
│   ├── produtos.js       guarda os produtos no navegador (CRUD + backup)
│   ├── logo-jalapao.svg  selo do cabeçalho
│   ├── logo-jalapao.png  ícone da aba
│   └── selo-jalapao.jpg  logo original com fundo creme
├── docs/                 esta documentação
├── design/               telas .dc.html + canvas do Claude Design
└── originais/            versões anteriores, antes do site
```

Não há build, framework nem dependência instalada. As páginas são HTML e JavaScript puro;
só duas coisas vêm de CDN, e só na página de etiquetas: o motor de OCR (Tesseract.js) e o
gerador de QR code.

## Design system

Tudo vem de `Jalapao Midia/Paleta_Jalapao_design_system.html`. Os tokens estão no topo de
`assets/jalapao.css` e são o **único** lugar para mexer em cor — nada de hex solto no meio
das páginas.

| Token | Uso |
|---|---|
| `--ground` `--surface` `--surface-alt` | fundos |
| `--ink` `--ink-soft` `--ink-faint` | texto |
| `--rule` `--rule-strong` | filetes e bordas |
| `--cerrado` `#c8670f` | dominante, **só em bloco** — nunca texto pequeno |
| `--accent` `#a54d0b` | botões e rótulo de seção |
| `--accent-deep` `#8f210b` | títulos e links |
| `--ok` `--bad` `--warn` | valores positivos, negativos e avisos |

Tipografia: Bahnschrift nos títulos e rótulos, serifada no corpo, Consolas em número e
código. O tema escuro acompanha o sistema operacional e usa os mesmos tokens — se você
acrescentar uma cor, acrescente nos dois blocos.

A regra de contraste da paleta vale aqui: texto branco sobre o laranja cerrado só passa em
tamanho grande. Para texto pequeno sobre bloco colorido, use o laranja queimado.

## Acrescentar uma ferramenta nova

1. Copie uma página existente — `impressao-3d.html` é a mais simples — e troque o miolo.
2. Ponha o link no menu de **todas** as páginas (o `<nav class="menu">` é repetido em cada
   uma; não existe include).
3. Marque a página atual com `aria-current="page"` no próprio menu dela.
4. Acrescente o cartão em `index.html`, com um ícone em SVG traçado — nunca emoji.
5. Atualize a tabela de páginas no `LEIA-ME.md` e escreva um documento em `docs/`.
6. Se quiser manter o canvas de design em dia, veja abaixo.

## O canvas de design

As telas existem como desenho editável em
<https://claude.ai/artifact/1ThGkYiqa72SKVSkZL69Ln>.

Os arquivos-fonte são os `.dc.html` de `design/`, mais o `canvas.json` que posiciona os
quadros. Para regerar e republicar depois de editar um deles, é preciso o Node instalado e
a skill do Claude Design — o comando monta um arquivo único a partir dos quatro desenhos e
do logo:

```
node seed-canvas.mjs --template payload.template.html --out sistema-jalapao-store.html \
  --title "Sistema Jalapão Store" \
  --artboard Main.dc.html --artboard Impressao3D.dc.html \
  --artboard Calculadora.dc.html --artboard Etiquetas.dc.html \
  --image ../assets/logo-jalapao.svg --canvas canvas.json
```

O canvas é desenho, não é o site: mudar lá não muda as páginas.

## Testar antes de dar por pronto

Abrir o arquivo com duplo clique já serve para quase tudo. Para testar como página servida
— o que o celular na mesma rede enxerga —, na pasta do projeto:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

e abra `http://127.0.0.1:8765/index.html`. O que vale conferir a cada mudança:

- todas as páginas abrem e o menu leva a todas;
- o logo aparece (é sinal de que a pasta `assets/` está sendo achada);
- tema claro e escuro;
- largura de celular — 375 px basta;
- nas calculadoras, um caso com resposta conhecida (os pedidos reais documentados em
  [calculadora de marketplace](calculadora-marketplace.md) e
  [custo de impressão 3D](custo-impressao-3d.md));
- salvar um produto e reabrir pela lista, se mexeu em `produtos.js` ou no formulário.

## Onde mora cada responsabilidade

A conta e o armazenamento vivem fora das páginas, em `assets/custo-3d.js` e
`assets/produtos.js`. As telas só leem campo, chamam essas funções e desenham o resultado.
Quem for mexer na fórmula ou no cadastro mexe no módulo — as duas páginas que dependem dele
(calculadora e lista) acompanham sozinhas. Detalhes do formato dos produtos em
[Produtos](produtos.md).

## Cache: js e css revalidam sempre

O `nginx-site.conf` manda `Cache-Control: no-cache` para `.css` e `.js`, e um dia de cache
só para imagem. Não é exagero: com `max-age=3600` nos scripts, um deploy deixava o HTML novo
rodando com o módulo antigo preso no navegador por até uma hora — foi assim que a lista de
produtos apareceu vazia depois de publicada a semente. `no-cache` não significa baixar tudo
de novo: o navegador reusa o arquivo depois de perguntar se mudou.

## Decisões que já foram tomadas

- **Nada de servidor, build ou dependência instalada.** O site abre com duplo clique. Um
  `.bat` que subia servidor local foi feito e descartado quando ficou provado que `file://`
  dá conta de tudo, inclusive do OCR e da escolha de pasta.
- **`originais/` guarda o passado.** A calculadora como estava antes do site e o gerador de
  etiquetas em arquivo único. O de etiquetas ainda tem uso: é a versão que vai para o
  celular sem precisar da pasta `assets/`.
- **Regra de negócio não se muda sozinha.** As taxas de marketplace só mudam com pedido
  explícito e, de preferência, conferidas contra um pedido real do painel.
