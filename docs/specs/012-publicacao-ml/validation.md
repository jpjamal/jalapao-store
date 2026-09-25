# Validação

## Automática
128 testes passando (20 novos em `apps/common/test_publicacao_ml.py`), com o Mercado Livre
de mentira:
- ordem das chamadas: valida → sobe fotos → cria → descrição;
- fotos vão como ids na ordem do rascunho; estoque real, sem o mínimo de 1; custo não sai;
- segundo pedido de publicação não chama o Mercado Livre e não duplica o `Listing`;
- sem estoque e rascunho inválido param antes das fotos;
- recusa na criação não grava vínculo; pedido de `family_name` na criação é atendido;
- falha na descrição vira aviso e mantém o anúncio;
- endpoint exige `publish_listingdraft`; `published_item_id` aparece depois;
- cliente real com HTTP gravado: corpo multipart, 201/400 da criação, descrição em `plain_text`.

`ruff`, `manage.py check`, `makemigrations --check` e contrato OpenAPI sem avisos. Frontend
compila com TypeScript limpo.


## Em produção, primeira publicação real (24–25/09/2026)

Rascunho do Dummy Aranha, 6 fotos JPEG 2304×2304 (0,5–0,8 MB), estoque 5, categoria
MLB264339. Quatro tentativas até publicar:

1. **Tela sem aviso.** O erro só aparecia no topo da página, longe do botão. Pelo tamanho da
   resposta (90 bytes), a mensagem era "O Mercado Livre recebeu a foto mas não devolveu o id
   dela." Não se soube o que o upload devolveu: ainda não havia log. Corrigido em 5ba89ac: erro
   também junto do botão, e o upload sem id passa a ir para o log.
2. **HTTP 503**, sem indicação da chamada. Corrigido em 40c2c66: todo erro do Mercado Livre vai
   para o log (método, caminho, corpo, sem token) e o upload tenta mais uma vez em 5xx.
3. **Fotos subiram.** A criação pediu `family_name` e, com ele, recusou `title`, com uma resposta
   400 **sem `cause`**: código em `message` (`body.invalid_fields`), texto em `error` ("The fields
   [title] are invalid for requested call."). A criação lia esses campos trocados e não tirava o
   `title`. Corrigido em ebaf5fe, com teste da sequência real.
4. **Publicado: MLB7700023302.** Criação com `family_name` e sem `title`: o Mercado Livre monta o
   título. `Listing` gravado com `user_product_id` MLBU5304860212, `family_id`
   493672865610577, estoque 5, `sync_enabled` falso.
5. **Descrição ausente no anúncio.** O rascunho tinha 842 caracteres, o `POST
   /items/{id}/description` não devolveu erro (nada no log), mas o dono não viu descrição no
   anúncio. Em vez de um botão avulso para a descrição, o rascunho publicado passou a ter
   **Salvar e enviar ao Mercado Livre**, que manda preço, fotos, atributos e descrição, e confere
   a descrição por `GET` depois de enviar.

Confirmado com a conta real: esta conta está no modelo User Products. **Na criação**, ela exige
`family_name` e recusa `title`, embora a simulação (`/items/validate`) aceite os dois.

Efeito colateral conhecido: cada tentativa que falhou depois do upload deixou fotos soltas na
conta do Mercado Livre, sem anúncio. Elas não aparecem para ninguém.

Em aberto: por que a descrição aceita não apareceu, e se o envio de alterações resolve; conferir no painel o
título montado pelo Mercado Livre e as fotos na ordem.
