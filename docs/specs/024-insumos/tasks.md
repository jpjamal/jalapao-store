# Tarefas

> Proposta: nada abaixo foi feito. Ordem sugerida, cada etapa entregável sozinha.

**Etapa 1 — cadastro de filamentos e escolha na peça 3D** (muda o custo)
- [x] App `supplies`: `SupplyCategory` (com as iniciais), `Supply`, regra do preço por grama e por kg
      e migração.
- [x] API e tela de cadastro de insumos e de categorias de insumo (lista, criar, editar, desativar,
      filtros).
- [x] `PrintingFilament` (linhas por peça), soma por linha em `pricing.py` e em `custo3d.ts` com os
      mesmos casos de teste, cópia do preço por grama, aviso de preço desatualizado e lista de
      linhas na tela da peça 3D e na ferramenta.
- [x] Testes e documentação.
- [ ] Conferir as telas com login e publicar (só quando o dono mandar).

**Etapa 2 — estoque em rolos e compra**
- [x] `SupplyStock`, `SupplyMovement`, `adjust_supply_stock`, baixa e ajuste com motivo.
- [x] `SupplyReceipt`, compra que entra no saldo e atualiza o preço do rolo, pagamento com saída
      única no caixa, `CashEntry.supply_receipt` e migração em `finance`.
- [x] Cancelar compra de insumo: serviço, estorno no caixa (`refund_of_supply_receipt`), preço do rolo
      e botão na tela.
- [x] Aba "Compras e movimentos" e coluna de saldo no cadastro.
- [x] Testes, documentação e validação com PostgreSQL.
- [ ] Conferir as telas com login e publicar (só quando o dono mandar).

**Etapa 3 — insumos na venda** (decisões do dono: avisar e baixar só o que tem; custo fora do lucro;
sem kit padrão; importadas do Mercado Livre não baixam)
- [x] Informar insumos usados ao criar a venda, com baixa no saldo na mesma transação.
- [x] Cancelar a venda devolve os insumos (só o que foi baixado).
- [x] Aviso do que faltou na resposta da API e na tela; insumos no histórico de vendas.
- [x] Testes, documentação e validação com PostgreSQL.
- [ ] Conferir as telas com login e publicar (só quando o dono mandar).

**Depois, só se o dono pedir**
- [ ] Alerta de pouco estoque, kit padrão por produto, custo de insumo no lucro e desconto automático de
      filamento por produção.

- [ ] Aprovação do dono.
- [ ] Publicação pelo GitHub (só quando o dono mandar).
