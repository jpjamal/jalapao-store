# Tarefas

- [x] Backend: módulos movidos para `domain/`, `api/`, `services/`, `infrastructure/`, `tests/`.
- [x] API de cada contexto em `serializers.py`, `permissions.py`, `views.py`, `urls.py`.
- [x] Regras puras extraídas (dinheiro, custo médio, totais da venda, SKU) com testes sem banco.
- [x] Validade da autorização da Shopee no adaptador; serviço sem detalhe de marketplace.
- [x] Settings por ambiente; CI com `config.settings.test` e `test apps`.
- [x] Frontend: `app/` só rotas, `features/<contexto>/`, `shared/`; `lib/api.ts` e
      `ml-anuncio.tsx` divididos.
- [x] `components.json` com os aliases novos.
- [x] Nginx de desenvolvimento: faltava `$jalapao_forwarded_proto` (erro anterior, visto ao
      recriar a cópia local).
- [x] Documentação: docs/architecture.md (organização, camadas, mapa antigo → novo), READMEs.
- [x] Publicar pelo GitHub (934b595 + c5baabb, 26/09/2026).
- [ ] Conferir as telas em produção por dentro, com login.
