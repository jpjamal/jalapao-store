# UI-001 — Gestão comercial

Objetivo: permitir operação de uma loja sem expor detalhes de infraestrutura ao operador.
Navegação permanente: Visão geral, Produtos, Estoque, Vendas, Caixa e Ferramentas.

Critérios: login inválido mostra erro; login válido leva ao painel. Cadastro não aceita
valores negativos; minutos entre 0 e 59. Backend valida todos os campos mesmo se o navegador
for contornado. Não limpar formulário em erro; desabilitar envio durante gravação. Listas
exibem estado vazio e paginação. Quantidade indisponível mostra o motivo da rejeição.
Nova venda recebe chave UUID persistente durante tentativa; sucesso gera nova chave.
Cancelamento pede confirmação pois repõe estoque e estorna caixa. Lançamento manual não
pode ser apagado; correção por lançamento inverso documentado.

Dados sensíveis não ficam no HTML estático nem em armazenamento local de produtos. Moeda
pt-BR, datas no fuso do navegador, banco UTC com contexto comercial America/Sao_Paulo.
Contraste de logotipo preservado em ambos os temas; layout usa tabelas com rolagem em telas pequenas.

Validação: build/TypeScript + fluxo manual no navegador de cadastro → estoque → venda →
recebimento → caixa; resumo da evidência em documentação de validação compartilhada.
