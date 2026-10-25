# 036 — Orçamento de peças 3D

Pedido do dono: às vezes é preciso enviar um orçamento de produto 3D. Escolher um ou vários produtos 3D e
gerar um documento para o cliente **sem custo**, só com o valor final, calculado pela porcentagem de lucro de
cada produto.

## Decisões do dono

- Não salvar: o orçamento é gerado na hora, sem número, lista nem banco.
- A margem de cada produto parte da cadastrada e pode ser ajustada no orçamento (porcentagem ou valor final).
- O documento traz: cliente e contato, validade, prazo de produção, observações, foto do produto, desconto e
  frete.
- Logo da Jalapão e Instagram **@storejalapao** no documento.

## Comportamento

- Ferramenta em **Ferramentas → Orçamento** (`/ferramentas/orcamento`).
- A escolha é **múltipla**: lista com caixas de marcação, busca, "Marcar todos" (os encontrados) e "Limpar
  marcados"; um botão adiciona todos os marcados de uma vez. Produto já no orçamento fica travado.
- Só aparecem produtos **3D** (os que têm parâmetros de impressão) e ativos.
- Cada item tem quantidade, margem de lucro (%) e valor unitário. O valor começa em
  `custo da peça × (1 + margem ÷ 100)`, com a margem do cadastro do produto. Mudar a margem recalcula o valor;
  mudar o valor recalcula a margem. Produto sem custo cadastrado parte do preço de venda, sem margem.
- Total = soma dos itens − desconto + frete.
- O documento mostra logo, Instagram, data de emissão, "válido até" (hoje + validade em dias), cliente,
  tabela de produtos (foto, nome, descrição curta, quantidade, valor unitário e total), totais, prazo e
  observações. **Custo e margem nunca aparecem nele.**
- **Baixar PDF** gera e baixa o arquivo direto (`orcamento-<cliente>-<data>.pdf`), em A4, com texto de
  verdade, logo, Instagram, fotos e paginação se passar de uma página. **Imprimir** abre o documento numa aba
  própria, de fundo branco, e chama a impressão do navegador.

## Compatibilidade

Só frontend: sem mudança de API, banco, estoque, Caixa ou contrato. Usa `GET /products` e
`GET /product-images`.

## Aceitação

Escolher um produto 3D e ver margem e valor coerentes; trocar a margem muda o valor e vice-versa; o
documento não mostra custo nem margem; desconto e frete entram no total; o PDF sai com logo e Instagram.
