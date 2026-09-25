# 014 — App instalável (PWA) com o ícone da marca

No celular, o Chrome oferecia só "Criar atalho" ("Não é possível instalar o app"): o sistema
não tinha manifesto nem ícones. Esta mudança torna o sistema instalável como app, com o
**logo colorido** da Jalapão Store.

## Comportamento

- **Android (Chrome, Samsung Internet):** menu ⋮ → **Instalar app**. O app abre em tela cheia,
  sem barra do navegador, com o ícone colorido na tela inicial e na lista de apps.
- **iPhone (Safari):** Compartilhar → **Adicionar à Tela de Início**, com o mesmo ícone.
- **Atalhos:** tocar e segurar o ícone no Android mostra Nova venda, Anúncios e Estoque.
- **Barra do sistema** na cor do tema: creme no claro, marrom-escuro no escuro.
- **Sem internet:** em vez da tela de erro do navegador, a página "Sem conexão" da loja, com
  o botão Tentar de novo.

## Decisões e limites

- **Nada é guardado offline.** Estoque, vendas e caixa são dados ao vivo; mostrar uma cópia
  antiga poderia levar a vender o que não existe. O service worker só guarda a página "sem
  conexão" e o ícone dela. API, páginas e imagens vão sempre à rede.
- **Ícone colorido** vem de `Jalapao Midia/logos_ate_1MB/logo_jalapao_store_colorido.png`,
  copiado para `frontend/brand/` (fonte, fora de `public/`: não é servido). Os PNGs do app são
  gerados por script, não à mão: `npm run icons`.
- **Ícone maskable** com o logo a 80% sobre o mesmo creme do logo (`#fdfae9`): o Android recorta
  o ícone em círculo, gota ou quadrado, e o selo precisa caber na zona segura sem emenda de cor.
- **Escopo `/jalapao-store/`**: o app abre e fica dentro do sistema; outros endereços do
  domínio (manuais em PDF) abrem no navegador.
- **Service worker só em produção**, para não atrapalhar o recarregamento em desenvolvimento.
- **Login continua valendo:** o app é o mesmo site; a sessão segue os mesmos cookies.
