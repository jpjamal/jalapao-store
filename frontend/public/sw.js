/* Service worker do app instalável (spec 014).
   Mínimo de propósito: o sistema trabalha com dados ao vivo (estoque, vendas, caixa), então
   nada da API nem das páginas é guardado. Só a página "sem conexão" e o ícone que ela usa,
   mostrados quando uma navegação falha por falta de rede.
   Trocar VERSAO sempre que offline.html ou o ícone mudarem. */
const VERSAO = "jalapao-v1";
const OFFLINE = "/jalapao-store/offline.html";
const ICONE = "/jalapao-store/icons/icon-192.png";

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll([OFFLINE, ICONE])));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((nomes) => Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n)))),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE)));
  } else if (new URL(request.url).pathname === ICONE) {
    event.respondWith(fetch(request).catch(() => caches.match(ICONE)));
  }
  // o resto (API, imagens, scripts) segue direto para a rede, sem passar por aqui
});
