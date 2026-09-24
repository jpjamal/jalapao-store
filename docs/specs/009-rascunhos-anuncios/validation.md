# 009 — Validação local

- `apps.common`: 82 testes passaram; 5 ignorados por requisitos específicos de banco/ambiente.
- Testes da spec: rascunhos independentes por canal, foto reutilizada, foto de outro produto
  rejeitada, arquivo inválido rejeitado, leitura da imagem exige autenticação e foto em uso
  não pode ser excluída.
- `makemigrations --check --dry-run`: nenhuma migração pendente.
- `ruff check`: passou para os arquivos alterados.
- `spectacular --validate --fail-on-warn`: passou; contrato versionado atualizado.
- `npm run build`: passou, incluindo rota `/anuncios`.

Validação somente local. Nenhum anúncio foi publicado; nenhuma chamada de estoque ocorreu.
Os novos modelos e a migração não foram aplicados à VPS nesta entrega.

## Revisão antes de publicar (24/09/2026)

Conferido no ambiente local completo (`docker compose up --build`), pelo mesmo caminho do
navegador — BFF do Next, Nginx, Django e volume:

- Login pelo BFF, upload de um PNG 640×480 em `multipart/form-data`: **201**.
- Leitura em `product-images/<id>/content`: **200**, `image/png`, conteúdo **idêntico byte a
  byte** ao enviado. Prova que o BFF deixou de ler o corpo como texto — o que corromperia
  qualquer binário — e passou a repassar `arrayBuffer`.
- Arquivo de texto com nome `.png`: **400**. A checagem é pelo conteúdo, com Pillow, não pela
  extensão.
- Backend recriado (`--force-recreate`), foto lida de novo: **200**, mesmos bytes. O volume
  `product_media` sobrevive ao que todo deploy faz.

Os limites fecham entre as camadas: 11 MB no BFF e no Nginx (`client_max_body_size 11m`),
10 MB por arquivo no Django. O Traefik não impõe limite de corpo.

Nenhuma foto de teste foi enviada em produção.
