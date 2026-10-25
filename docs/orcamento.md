# Orçamento de peças 3D

Gera um orçamento para enviar ao cliente, com um ou vários produtos 3D e **só o valor final** — o custo
e a margem não aparecem. Spec [036](specs/036-orcamento-de-pecas-3d/spec.md).

## Como usar

1. **Ferramentas → Orçamento.** A lista mostra os produtos 3D com caixa de marcação: marque quantos quiser
   (a busca filtra por nome ou código; *Marcar todos* pega todos os encontrados) e toque em
   *Adicionar N ao orçamento* — todos entram de uma vez. Os já adicionados ficam travados como "No orçamento".
2. Em cada item, defina a **quantidade** e ajuste a **margem de lucro (%)** ou o **valor unitário**: um
   recalcula o outro. A margem começa na cadastrada no produto.
3. Preencha cliente, contato, validade (dias), prazo de produção, observações, desconto e frete.
4. Confira o orçamento na própria tela e use **Gerar PDF / imprimir**: abre uma aba com o documento e a
   janela de impressão do navegador, onde se escolhe *Salvar como PDF*.

## Regras

- Só entram produtos **3D** ativos (os que têm parâmetros de impressão).
- Valor unitário = custo da peça × (1 + margem ÷ 100). Sem custo cadastrado, parte do preço de venda.
- Total = itens − desconto + frete. Nada é gravado: não há número, lista nem histórico de orçamentos.
- O documento traz logo e Instagram @storejalapao, emissão, validade, cliente, fotos, prazo e observações.

Ver também [custo de impressão 3D](custo-impressao-3d.md) e [produtos](produtos.md).
