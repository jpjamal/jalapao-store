# Validação

## Automatizada (24/10/2026)

- `npm run typecheck`: aprovado.

## Conferência local (cópia com dados de teste descartáveis)

- Só o produto 3D aparece para escolher (o de revenda fica de fora).
- Produto com custo 20 e margem 150%: valor unitário R$ 50,00; margem 100% → R$ 40,00; valor R$ 60,00 →
  margem 200%.
- Escolha múltipla: marcar 2 de 4 produtos e adicionar de uma vez; "Marcar todos (2)" adicionou os outros
  dois; os adicionados aparecem como "No orçamento" e sem caixa livre; total somou os 4 itens (R$ 118,00).
- Documento com cliente, desconto de R$ 5,00 e frete de R$ 12,50: subtotal 50,00 → total 57,50; mostra logo
  (carregou), Instagram @storejalapao, emissão e validade; não contém "custo", "margem" nem "lucro".
- Não conferido: a janela de impressão/PDF (o navegador do teste não abre a caixa de impressão), a foto do
  produto no documento e o celular.

## Publicação

Publicada em 24/10/2026 em https://jpsys.duckdns.org/jalapao-store (e pelo IP).

Pendente: gerar um orçamento real em produção e conferir o PDF impresso (foto, logo, celular).
