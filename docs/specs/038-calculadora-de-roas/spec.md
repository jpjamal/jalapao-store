# 038 — Calculadora de ROAS

Pedido do dono: ter na Jalapão Store a mesma calculadora de ROAS do site Conectando Vendedores
(conectandovendedores.com.br/calculadora-de-roas), junto da ferramenta de taxas de marketplace.

## O que é ROAS aqui

Quanto o anúncio vende para cada R$ 1 gasto nele. A conta do site, reproduzida igual:

- Lucro líquido = preço de venda − preço de compra − custos da operação − taxa do marketplace
  (`preço × % + taxa fixa`) − impostos (`preço × %`) − frete.
- **ROAS de empate** = preço ÷ lucro (o anúncio gasta 100% do lucro). **Visibilidade** = preço ÷ (lucro × 50%).
  **Rentabilidade** = preço ÷ (lucro × X%), com X padrão 10%.
- **ROAS atual** = preço ÷ gasto atual por venda. Classificação: gasto maior que o lucro → *Perdendo*; senão,
  ROAS atual ≥ rentabilidade → *Rentabilidade*; ≥ visibilidade → *Visibilidade 50%*; senão → *Empate*.

## Ferramenta

- **Ferramentas → Calculadora de ROAS** (`/ferramentas/roas`), ao lado das Taxas de marketplace. A calculadora
  de taxas ganhou o atalho "Calcule o ROAS do anúncio".
- Campos iguais aos do site: preço de compra, custos da operação, preço de venda, taxa do marketplace (%),
  taxa fixa (R$), impostos (%), frete (opcional), % do lucro para a rentabilidade e gasto atual por venda.
- **Diferença para o site:** um seletor "Taxas do marketplace" (Shopee, Mercado Livre Clássico ou Premium) preenche
  a taxa e a taxa fixa pelo preço de venda, com as **mesmas regras da calculadora de taxas** (faixas da
  Shopee; 13% / 17,5% e R$ 6,50 abaixo de R$ 79 no Mercado Livre). Em "Digitar as taxas" os campos são livres.
- Cada ROAS mostra também o gasto máximo por venda que ele permite (a parte do lucro).
- **Lucro zero ou negativo:** o site mostra ROAS negativo; aqui aparece "—" com o aviso de que nenhum gasto em
  anúncio se paga (a classificação *Perdendo* continua valendo).

## Compatibilidade

Só frontend, sem API nem banco; nada é gravado. Fórmulas em `frontend/src/features/tools/lib/roas.ts`.

## Aceitação

Mesmos números do site para os mesmos dados; trocar o marketplace preenche e trava a taxa; sem lucro mostra o
aviso; classificação muda com o gasto atual.
