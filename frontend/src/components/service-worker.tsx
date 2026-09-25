"use client";
import { useEffect } from "react";
import { BASE } from "@/lib/api";

/* Registra o service worker do app instalável (public/sw.js). Só em produção: em
   desenvolvimento ele atrapalharia o recarregamento automático. */
export function ServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register(`${BASE}/sw.js`, { scope: `${BASE}/` }).catch(() => {
      // sem service worker o sistema funciona igual; só não mostra a página "sem conexão"
    });
  }, []);
  return null;
}
