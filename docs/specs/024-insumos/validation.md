# Validação

## Etapa 1 — categorias e cadastro de insumos, filamentos multicolor (30/09/2026)

- Suíte completa (227 testes, 30 deles novos) contra PostgreSQL 17 real: OK. `ruff`,
  `manage.py check`, contrato OpenAPI validado com `--fail-on-warn` (a única linha removida é
  `weight_g` da lista de obrigatórios do perfil 3D, agora opcional quando há linhas),
  ausência de migrações pendentes, `tsc --noEmit` e `next build`: OK.
- Conta multicolor, conferida com os mesmos números no backend (teste) e na ferramenta do frontend
  (executada à parte com Node): 30 g de um rolo de R$ 100,00/1.000 g mais 12 g de um de
  R$ 89,90/1.000 g dão R$ 4,0788 de filamento; com 2 h a 200 W e R$ 1,56 o kWh, custo R$ 4,70 e
  preço sugerido R$ 9,41. Uma linha só dá o mesmo resultado da conta de sempre, e a peça sem linhas
  continua em R$ 5,80 / R$ 11,60. O preço por grama não é arredondado: só o total vira centavos.
- Testes de insumos: preço por grama e por kg (inclusive rolo que não dá casa decimal exata),
  material com a grafia sugerida, categorias (nome único sem diferenciar acento, trava de
  `is_filament`, sem DELETE), insumo de filamento exigindo material, cor, peso e preço do rolo,
  insumo comum recusando esses campos, nome único dentro da categoria, troca de categoria só entre
  as do mesmo tipo, categoria inativa, filtros, sugestões de material e permissões.
- Testes das linhas na peça: custo, peso e preço médio ponderado; mudar o preço do filamento não
  altera peças existentes e só marca `price_outdated`; `refresh_price` traz o preço atual; editar
  gramas e remover linha recalcula; voltar ao modo manual mantém o peso; peça sem linhas inalterada;
  peso ou linhas obrigatórios; linha repetida, sem gramas, acima de 8 linhas, insumo que não é
  filamento e filamento inativo recusados; filamento inativo continua em peça que já o usa.
- Na tela, com o app local (SQLite): `/insumos` lista as 7 categorias iniciais; cadastro de um
  filamento mostra a prévia de R$ 0,10 por grama e R$ 100,00 por kg, grava o material como "PLA" e
  lista os dois valores; peça multicolor salva pelo formulário de produto com duas linhas (42 g,
  filamento R$ 4,08); ao dobrar o preço de um rolo o custo da peça continuou R$ 4,08 e a edição
  mostrou o aviso "O preço deste filamento mudou"; a ferramenta de custo 3D com as mesmas duas
  linhas deu custo R$ 4,70 e preço R$ 9,41 e escondeu o preço por kg e o peso digitados.
- Dois defeitos do próprio formulário apareceram nessa conferência e foram corrigidos: a linha de
  filamento era recriada ao escolher o filamento (chave do React), e o campo de gramas tinha
  `step="0.1"` com `min="0.001"`, o que fazia o navegador recusar 30 g.
- Os dados criados no teste foram removidos do banco local; as 7 categorias iniciais ficam, como
  em qualquer instalação.

## Limites da evidência
As telas foram conferidas por automação no painel do navegador (cliques por script, porque o painel
ficou oculto), sem celular nem tema escuro e sem usuário que não seja superusuário na tela (as
permissões foram testadas na API). Não há estoque, compra nem baixa de insumo: são a etapa 2. O
valor de estoque e o lucro dos produtos não mudam.

## Etapa 2 — estoque em rolos, compras, pagamento e cancelamento (30/09/2026)

- Suíte completa (248 testes, 21 deles novos da etapa 2) contra PostgreSQL 17 real, **sem nenhum teste
  pulado** (inclui o teste de concorrência de insumos): OK. Em SQLite, o de concorrência é pulado,
  como os outros. `ruff`, `manage.py check`, contrato OpenAPI validado com `--fail-on-warn`, ausência
  de migrações pendentes, `tsc --noEmit` e `next build`: OK.
- Testes do serviço: saldo inteiro que nunca fica negativo, baixa e ajuste exigindo motivo e
  quantidade diferente de zero, insumo inativo dando baixa mas recusando entrada; compra que entra no
  saldo e fica a pagar, idempotência (mesma chave, e recusa da mesma chave com outro conteúdo),
  compra de filamento atualizando o preço do rolo e compra de outro insumo não mexendo em preço;
  pagamento que gera uma só saída e recusa data futura; cancelamento que devolve o saldo sem apagar a
  compra, estorno único no caixa (mesmo cancelando duas vezes), recusa depois de baixa ou de nova
  compra sem alterar nada, compra mais recente ainda cancelável, compra cancelada que não se paga, e
  preço do rolo que só volta ao de antes se não foi editado.
- Testes da API: saldo na listagem, baixa e ajuste pelo endpoint de movimentos, pagamento e
  cancelamento (resposta sem `request_hash`), recusa de cancelamento em 400 no campo `receipt`, data
  futura e insumo inativo recusados, e permissões em cada ação.
- Concorrência (PostgreSQL): duas compras com a mesma chave viram uma só, dois pagamentos
  simultâneos geram uma só saída no caixa e, com saldo 1, só uma de duas baixas simultâneas passa.
- Na tela, com o app local: as duas abas e a coluna de saldo; comprar 10 pacotes a R$ 3,50 (saldo 10,
  compra a pagar); dar baixa de 2 (saldo 8); na aba Compras e movimentos, a compra e os dois
  movimentos aparecem; pagar gerou a saída "Insumo: Caixa pequena" de R$ 35,00 no caixa, uma vez;
  tentar cancelar essa compra depois da baixa foi recusado com a mensagem de explicação e nada
  mudou; uma compra de filamento a R$ 89,90 paga e cancelada deixou saldo 0, devolveu o preço do
  rolo a R$ 100,00, gerou o estorno de entrada de R$ 89,90 e ficou como "Cancelada".
- Os dados criados no teste foram removidos do banco local, inclusive os lançamentos de caixa dele.

## Limites da evidência da etapa 2
As telas foram conferidas por automação no painel (cliques por script, porque o painel ficou
oculto), sem celular nem tema escuro e sem usuário sem permissão de superusuário na tela (as
permissões foram testadas na API). O teste de concorrência só roda em PostgreSQL. Ainda não há
insumos na venda nem alerta de pouco estoque.

## Etapa 3
Pendente: nada implementado.
