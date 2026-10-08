# 030 — Corrigir e excluir vendas

Pedido do dono: corrigir canal e valores digitados por engano. Exclusão aprovada com histórico
interno, devolução dos produtos e insumos e estorno do recebimento; não apagar registros.

## Comportamento
- Editar uma venda confirmada permite corrigir canal, referência, preço unitário de cada item,
  desconto, taxa e frete. Produtos, quantidades, insumos e custos congelados não mudam.
- Recalcular bruto, líquido e lucro usando a mesma regra da criação. Valores negativos ou
  descontos/taxas/frete que excedam o bruto são recusados sem efeitos.
- Venda a receber: atualizar o valor a receber, sem lançamento no caixa. Venda recebida:
  lançar apenas a diferença no caixa, entrada ou saída, na data da correção. Preservar o
  recebimento original e identificar o ajuste como automático, fora das despesas manuais.
- Toda edição guarda autor, data e valores antes/depois. Uma versão desatualizada da venda
  é recusada; repetir a mesma solicitação não duplica ajuste. Cancelamento posterior estorna
  o líquido corrigido e devolve exatamente os custos e insumos originais.
- Excluir pede confirmação explícita com os efeitos. Cancela se necessário, registra quem
  excluiu e a data, e retira da listagem normal. Excluir novamente ou excluir venda já cancelada
  não repete estoque/estorno. O histórico fica disponível no Admin, somente leitura.
- Venda cancelada ou excluída não pode ser editada nem recebida. Venda excluída não conta
  no painel nem nas contas a receber.
- Correção local de canal mantém a origem e o número de pedido importado separados: não
  altera o marketplace e não permite reimportar uma venda corrigida ou excluída.
- Edição exige alterar venda; acerto de venda recebida também exige lançar caixa. Exclusão
  exige excluir/alterar venda, movimentar estoque/caixa e devolver insumos quando usados.

## Interface
Botões Editar e Excluir no histórico. Editor abre visível com valores atuais, aviso de acerto
no caixa para venda recebida e erros junto do formulário. Exclusão usa janela de confirmação.
Cancelamento existente permanece disponível. Busca, filtros e ordenação são preservados.

## Não objetivos
Trocar itens/quantidades/insumos, alterar datas, apagar histórico físico, desfazer exclusão,
editar vendas canceladas, correção remota no marketplace, mudanças em compras ou ferramentas.

## Aceitação
Testar edição antes/depois de receber, preços/desconto/taxa/frete, custo congelado, caixa com
diferenças positivas/negativas/zero, cancelamento depois de várias correções, exclusão repetida,
insumos parcialmente consumidos, permissões, concorrência, versão desatualizada, repetição da
requisição, pedido importado e regressões. Validar migrações, contrato, build e tela.
