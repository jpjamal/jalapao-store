# 036 — Máscara nos campos numéricos

Pedido do dono: todos os campos numéricos passam a ter máscara no padrão brasileiro, para digitar e conferir
valores sem erro no celular.

## Comportamento

- **Dinheiro** (campos com passo de centavos): os dígitos entram pela direita, como na maquininha —
  `5` vira `0,05` e `123456` vira `1.234,56`.
- **Outros decimais** (peso, energia, percentual, potência): digita-se com vírgula, com ponto de milhar e
  limitado às casas decimais do campo. Um ponto digitado logo após até três dígitos vale como vírgula.
- **Inteiros** (quantidade, horas, minutos, ajuste de estoque): só dígitos, com ponto de milhar. O ajuste de
  estoque aceita sinal de menos.
- O teclado do celular abre numérico quando o campo não aceita negativos.
- O mínimo continua validado no envio (mensagem do próprio formulário) e o máximo impede digitar acima dele.
- `form.reset()` devolve o campo ao valor inicial.

## Compatibilidade

Só apresentação. O valor lido pelo restante do app e enviado à API continua o número puro (`1234.56`);
nenhuma API, cálculo, estoque ou Caixa muda. A máscara vive em `shared/ui/number-input.tsx` e é aplicada
por `Input type="number"`, logo cobre todas as telas, inclusive as ferramentas.

## Não objetivos

Campos de código (GTIN, SKU) e datas não têm máscara numérica.

## Aceitação

Em cada tela com valor numérico: digitar, editar com backspace, salvar e reabrir mostram o mesmo valor
formatado; o que chega à API é o número puro. Rodar typecheck e build.
