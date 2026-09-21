# Sistema Jalapão Store

Site interno da loja: as ferramentas do dia a dia, em HTML e JavaScript puro, sem build e
sem dependência instalada.

**No ar:** <http://217.216.82.25/jalapao-store/>
**Manuais de produto:** <http://217.216.82.25/manuais/>

Para usar sem servidor, é só abrir `site/index.html` com duplo clique — funciona igual.

## Páginas

| Arquivo | O que faz |
|---|---|
| `site/index.html` | Início, com as ferramentas |
| `site/impressao-3d.html` | Custo da peça impressa (filamento + energia + trabalho) e preço com margem |
| `site/produtos-3d.html` | Lista das peças já calculadas, para consultar e editar |
| `site/calculadora.html` | Lucro líquido depois das taxas da Shopee e do Mercado Livre |
| `site/etiquetas.html` | `.txt` de ZPL do pedido → um PDF por etiqueta, nomeado pelo cliente |

## Estrutura

```
site/        o que o nginx publica em /jalapao-store
manuais/     PDFs públicos em /manuais — enviados por SSH, fora do repositório
docs/        documentação das ferramentas (não vai para o ar)
design/      as telas desenhadas no Claude Design (não vai para o ar)
```

## Documentação

- [Calculadora de marketplace](docs/calculadora-marketplace.md) — as taxas da Shopee e do
  Mercado Livre, de onde saem e o que não entra na conta
- [Custo de impressão 3D](docs/custo-impressao-3d.md) — as fórmulas e as pegadinhas
- [Produtos](docs/produtos.md) — como salvar e editar uma peça, e como fazer backup
- [Gerador de etiquetas](docs/gerador-de-etiquetas.md) — por que precisa de OCR e como nomeia
- [Manutenção](docs/manutencao.md) — cores, tokens e como acrescentar uma ferramenta

## Deploy

`push` na `main` dispara o GitHub Actions, que faz `rsync` do repositório para o servidor e
sobe o container com `docker compose`. O Traefik entrega em `/jalapao-store` sem remover o
prefixo — é por isso que o site mora numa pasta com esse nome dentro do nginx.

Para publicar um manual novo (não passa pelo Git, é envio direto):

```bash
scp -i ~/.ssh/stack_deploy manual.pdf deploy@217.216.82.25:~/jalapao-store/manuais/
```

A pasta `manuais/` está na lista de exclusões do `rsync --delete` justamente para que o
deploy não apague os PDFs enviados assim.

## O que roda onde

As contas rodam no navegador. A **lista de produtos 3D fica no servidor** (`/api/produtos`,
dados em `~/jalapao-store/dados/`), então ela é a mesma em qualquer aparelho: ler é aberto,
gravar pede a senha guardada em `dados/senha.txt`. O gerador de etiquetas conversa direto
com a API do Labelary a partir do navegador — nenhum arquivo de pedido passa pelo servidor.

## Histórico

Este repositório hospedava o Streamlit de gestão da loja (produtos, compras, vendas,
estoque). Ele foi aposentado em 21/09/2026; o código está na tag `streamlit-legado` e os
dados em `data/`.
