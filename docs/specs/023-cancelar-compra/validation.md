# Validação

Em 29/09/2026:

- Suíte completa (197 testes, 10 deles novos) contra PostgreSQL 17 real: OK. `ruff`,
  `manage.py check`, contrato OpenAPI validado com `--fail-on-warn` (só linhas novas, sem
  mudança nas existentes), ausência de migrações pendentes, `tsc --noEmit` e `next build`: OK.
- Testes do serviço: estoque com entrada antiga de outro custo volta exatamente a 2 unidades e
  R$ 20,00 ao cancelar a de R$ 100,00; compra sem pagamento não mexe no caixa; compra paga gera
  um só estorno mesmo cancelando duas vezes; produção não mexe no caixa; recusa depois de venda,
  ajuste ou nova entrada, sem alterar nada; a entrada mais recente ainda cancela; compra
  cancelada não pode ser paga.
- Testes da API: cancelamento com a entrada listada como cancelada, recusa com mensagem no campo
  `receipt` (400) e recusa por falta de permissão (403).
- Na tela, com o app local e SQLite: compra paga de 4 unidades a R$ 7,50 cancelada pelo botão.
  A confirmação descreve o efeito; a linha passou a "Cancelada" e o botão sumiu. O estoque voltou
  aos 15 unidades e R$ 210,00 de antes e o caixa ganhou "Estorno de compra" de entrada de
  R$ 30,00. Cancelar uma entrada antiga mostrou a mensagem de recusa e não mudou nada.
- Os dados criados nesse teste foram removidos do banco local depois.

## Limites da evidência
Só cancela se a entrada for a última movimentação do produto; depois de uma venda ou ajuste a
correção passa pelos ajustes de estoque (decisão de projeto, registrada na spec). O caminho do
cancelamento não foi conferido em celular nem com usuário sem permissão de superusuário na tela
(a permissão foi testada só na API). A venda já tinha cancelamento e não foi alterada.
