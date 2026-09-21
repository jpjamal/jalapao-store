# Produtos

`produtos-3d.html` — a lista do que já teve o custo calculado, e o lugar de onde se reabre
uma peça para refazer a conta.

## Como usar

1. Na página de **impressão 3D**, faça a conta da peça normalmente.
2. Dê um **nome do produto** no topo e clique em **Salvar produto**.
3. A peça passa a aparecer em **Produtos**, com custo e preço sugerido.

Para mexer depois, clique em **Editar** na lista: a calculadora abre com tudo preenchido e o
botão vira *Salvar alterações*. Ali você ainda tem:

- **Salvar como novo** — grava uma cópia com as alterações e mantém o original intacto. Útil
  para variações de tamanho da mesma peça.
- **Cancelar edição** — solta o produto e volta ao modo de peça nova.

Na lista você também pode **duplicar** (cria uma cópia com "(cópia)" no nome) e **excluir**.

A lista tem busca por nome e quatro ordens: mais recentes, nome, maior preço e maior custo.
No rodapé ela soma quantos produtos existem, o custo somado, o filamento total e as horas
de impressora — útil para ter noção do estoque de trabalho.

O rótulo **incompleto** marca a peça que foi salva com algum campo obrigatório em branco
(preço do filamento, gramas, consumo, tempo ou kWh). Ela fica guardada do mesmo jeito, só
avisa que o preço ali não vale.

## Onde os dados ficam

No **localStorage do navegador**, nesta máquina. Não sobem para lugar nenhum, não são
compartilhados entre computadores e ninguém mais enxerga.

Três consequências que valem saber:

- Trocar de navegador ou de computador **não leva a lista junto**.
- Limpar "dados de sites" do navegador apaga os produtos.
- Abrir o site por caminhos diferentes cria listas diferentes: o arquivo aberto direto do
  disco (`file://`) e o mesmo site servido por `http://localhost` são endereços distintos
  para o navegador, cada um com seu armazenamento.

Por isso existe o **backup**. Na página de produtos:

- **Baixar backup** gera um `.json` com tudo (o nome do arquivo já vem com a data).
- **Restaurar backup** lê esse arquivo e junta ao que já existe — produto com o mesmo id é
  substituído, os demais entram como novos. Nada é apagado no caminho.

Vale baixar um backup de vez em quando e guardar junto das artes, no OneDrive.

## O formato

Um produto salvo é assim:

```json
{
  "id": "p_mu1kfrzr_rdghq",
  "tipo": "impressao3d",
  "nome": "Luminária capim dourado",
  "criadoEm": "2026-09-14T18:17:54.806Z",
  "atualizadoEm": "2026-09-14T18:17:54.806Z",
  "entradas": {
    "precoKg": "115", "gramas": "45",
    "consumo": "200", "horas": "5", "minutos": "18", "kwh": "1.56",
    "maoDeObra": "", "custoFixo": "", "margem": "100"
  }
}
```

Duas decisões importantes aqui:

- **Só as entradas são guardadas, nunca o resultado.** Custo e preço são recalculados toda
  vez que a lista é desenhada. Assim, se a fórmula mudar ou você corrigir o valor do kWh, os
  produtos antigos passam a mostrar o número certo sozinhos — não fica preço velho
  congelado no cadastro.
- **`tipo` já existe desde o começo.** Hoje só há `impressao3d`, mas quando entrar produto
  de revenda ou outra família, cada um filtra o que é seu com `Produtos.listar(tipo)`.

O arquivo inteiro é versionado (`versao: 1`). Quando o formato mudar, a função `migrar()`
em `assets/produtos.js` conserta os registros antigos na hora de ler — quem já tinha
produtos salvos não perde nada.

## A semente: como os produtos viajam no deploy

A lista mora no navegador, então ela **não** acompanha o site sozinha — quem abrisse o
endereço numa máquina nova encontraria a lista vazia. Quem resolve isso é
`site/assets/produtos-seed.js`, versionado no repositório.

Ele é plantado uma vez por versão, com três garantias:

- item cujo `id` já existe é ignorado — **o que você cadastrou nunca é sobrescrito**;
- depois de plantada, a versão fica marcada no navegador, então peça apagada de propósito
  não ressuscita no deploy seguinte;
- quando uma versão **nova** da semente é publicada, ela planta o que estiver faltando. Como
  a semente é gerada a partir do seu próprio backup, o que você apagou não está lá e não
  volta.

Para atualizar a semente depois de cadastrar peças novas: **Baixar backup** na página
Produtos, e me peça para regerar — ou cole os itens no arquivo e troque a data em `versao`.

É um `.js` e não um `.json` de propósito: arquivo aberto com duplo clique (`file://`) não
consegue fazer `fetch` de JSON, o navegador bloqueia. Como script, funciona nos dois casos.

## Para crescer

O trabalho já está separado em dois módulos, justamente para não precisar mexer nas telas
quando o cadastro crescer:

| Arquivo | Responsabilidade |
|---|---|
| `assets/custo-3d.js` | só a conta: recebe as entradas, devolve custo, lucro e preço |
| `assets/produtos.js` | só o armazenamento: listar, obter, salvar, remover, duplicar, backup |

**Acrescentar um campo novo** (foto, categoria, link do anúncio, preço praticado na Shopee,
quantidade em estoque) é:

1. colocar o campo no formulário da calculadora;
2. incluir o nome dele na constante `CAMPOS` — se for dado de impressão — ou passar direto
   no objeto de `Produtos.salvar()`, se for informação do produto;
3. mostrar a coluna na lista, se fizer sentido;
4. se registros antigos precisarem de valor padrão, tratar em `migrar()`.

Nada disso mexe no que já está salvo.

**Ideias que o formato já aguenta**, para quando fizer falta: foto da peça (guardada como
data URI ou caminho de arquivo), categoria, tempo de acabamento separado do de impressão,
histórico de preço, vínculo com o anúncio do marketplace, e um botão que joga o custo do
produto direto no campo de custo da calculadora de marketplace.
