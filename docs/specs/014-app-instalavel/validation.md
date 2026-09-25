# Validação

## Cópia local (localhost:8080, código atual)
- `/jalapao-store/manifest.webmanifest` responde com `display: standalone`, `start_url` e
  `scope` em `/jalapao-store/`, 3 ícones (dois `any`, um `maskable`) e 3 atalhos.
- Os 5 ícones, `sw.js` e `offline.html` respondem 200 com o tipo certo; `sw.js` sai com
  `Cache-Control: public, max-age=0`, então versão nova do service worker é vista na hora.
- As páginas trazem `<link rel="manifest">`, `<link rel="apple-touch-icon">` e as duas
  `<meta name="theme-color">` (claro e escuro).
- Ícone maskable conferido visualmente: selo inteiro dentro da zona segura, fundo contínuo.
- TypeScript limpo.

## Limites da evidência
O registro do service worker **não pôde ser conferido** no navegador embutido usado nos testes:
ele recusou com "An unknown error occurred when fetching the script", mesmo com o arquivo
servido corretamente — comportamento de navegador embutido sem suporte a service worker. A
instalação e a página sem conexão ficam para conferir no Android do dono.
