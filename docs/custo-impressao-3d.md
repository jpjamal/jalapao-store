# Custo de impressão 3D

`impressao-3d.html` — o que a peça custou de filamento, energia e trabalho, e por quanto
sai com margem.

A conta é a mesma da [calculadora da 3D Prime](https://3dprime.com.br/calculadora-de-custo-de-impressao-3d/),
lida direto do código da página deles em 14/09/2026. A parte de gerar orçamento em PDF
ficou de fora de propósito.

## A conta

```
filamento = (preço do quilo ÷ 1000) × gramas usados
energia   = (watts × horas ÷ 1000) × valor do kWh
total     = filamento + energia + mão de obra + custos fixos
lucro     = total × margem
preço     = total + lucro
```

Sem margem, o resultado grande é o **custo da impressão**. Com margem, vira **preço final
sugerido** e aparece a linha do lucro.

## Os campos

| Campo | Observação |
|---|---|
| Preço do filamento (R$/kg) | o que você pagou no rolo |
| Filamento usado (g) | o fatiador informa |
| Consumo da impressora (W) | atalhos: Ender 3 · 120 W, Bambu A1 · 200 W, Bambu X1C · 350 W |
| Tempo — horas e minutos | veja a pegadinha abaixo |
| Valor do kWh | atalhos por bandeira: verde 0,65 · amarela 0,80 · vermelha 1,00 |
| Mão de obra (R$) | valor fixo por peça: preparação, acabamento |
| Custos fixos (R$) | desgaste da impressora, bico, lixa, cola |
| Margem de lucro (%) | atalhos de 30, 50, 80 e 100% |

### A pegadinha do tempo

O fatiador e a calculadora da 3D Prime trabalham em **hora decimal**: `2,3 h` não é duas
horas e trinta, é **2 h e 18 min**. Por isso aqui o tempo tem dois campos separados. Se
preferir, dá para digitar `2,3` no campo de horas e deixar os minutos vazios — o resultado
é o mesmo.

Isso já causou confusão uma vez: o mesmo pedido dava R$ 0,72 de energia lá e R$ 0,79 aqui,
só porque 2,3 h tinha virado 2 h 30 min.

### Salvar a peça como produto

O campo **nome do produto**, no topo, guarda a conta inteira na lista de
[Produtos](produtos.md) — inclusive para editar depois. Sem nome, a calculadora funciona
igual; o nome só é exigido na hora de salvar.

### O que fica guardado

Preço do filamento, consumo em watts, valor do kWh, mão de obra e margem ficam salvos no
navegador e voltam preenchidos na próxima vez — são dados da sua máquina, não da peça. O
botão **Limpar** zera só o que muda de peça para peça: gramas, tempo e custos fixos.

## Verificação

Conferido contra um print da calculadora da 3D Prime, com 115 R$/kg, 45 g, 200 W, 5,3 h,
kWh 1,56 e margem de 100%:

| | 3D Prime | Aqui |
|---|---|---|
| Filamento | 5,17 | 5,18 |
| Energia | 1,65 | 1,65 |
| Custo total | 6,83 | 6,83 |
| Preço final | 13,66 | **13,66** |

A diferença de um centavo no filamento é arredondamento: a conta dá 5,175 e o `toFixed` do
site deles corta para baixo por causa da representação binária do número, enquanto aqui
arredonda para cima. O total e o preço final são idênticos.

## O que não entra

- **Falhas de impressão.** Se 1 em cada 10 peças vai para o lixo, some isso na margem ou
  nos custos fixos.
- **Depreciação real da máquina.** O campo de custos fixos é uma estimativa sua, não um
  cálculo de vida útil do equipamento.
- **Material de suporte e purga** contam como gramas — use o número do fatiador, que já
  inclui.
- **Imposto e taxa de marketplace.** Para saber se o preço fecha na Shopee, jogue o
  resultado daqui no campo de custo da [calculadora de marketplace](calculadora-marketplace.md).
- **Seletor de material.** Na página da 3D Prime ele serve para puxar o preço do filamento
  da loja deles; aqui o preço é seu para preencher.

## Sobre o consumo em watts

Os valores dos atalhos são médias da impressora com bico e mesa quentes, não medição. Quem
quiser o número certo mede com um wattímetro de tomada e guarda o valor no campo — ele fica
salvo.
