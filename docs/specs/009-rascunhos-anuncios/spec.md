# 009 — Catálogo de imagens e rascunhos de anúncios

## Objetivo

Permitir preparar fotos e conteúdo comercial de um produto antes de publicá-lo em um
marketplace. O produto, seu SKU, custo e saldo continuam independentes dos anúncios.

## Modelo proposto

- `Product` representa o item físico. Nome, SKU, tipo, custo, preço de referência e estoque
  continuam válidos mesmo sem fotos, descrição ou anúncio.
- `ProductImage` pertence a um produto e guarda arquivo original, posição, texto alternativo,
  metadados técnicos e data de inclusão. As fotos podem ser reutilizadas em vários canais.
- `ListingDraft` pertence a um produto e a um canal. Guarda título sugerido, descrição,
  preço proposto, condição, categoria, marca, modelo e atributos específicos do canal.
  Campos comerciais são opcionais enquanto é rascunho.
- `ListingDraftImage` ordena as imagens escolhidas para cada rascunho, permitindo capa e ordem
  diferentes entre canais sem duplicar o arquivo.
- `Listing` continua representando apenas um anúncio remoto efetivo, identificado por
  `item_id`/vendedor/canal. O vínculo do rascunho com ele pertence à etapa de publicação.

## Regras de domínio

- Um produto pode ter nenhum ou um rascunho por canal nesta versão. Pode ter mais de um
  anúncio remoto por canal; a ampliação dos rascunhos depende de um caso concreto.
- SKU identifica o produto/variante e não inclui quantidade. Estoque é a fonte local única.
- Nome interno do produto não muda quando o título de um anúncio é editado.
- Custo interno nunca é enviado ao marketplace. Preço de anúncio é decisão comercial.
- Atributos de categoria específicos ficam em JSON no rascunho; os campos compartilhados e
  pesquisáveis têm colunas próprias. A interface de atributos será feita na etapa de validação.
- Rascunho incompleto pode ser salvo. A validação de obrigatoriedade ocorre na ação de
  validar/publicar para o canal escolhido, consultando regras atuais do marketplace.
- Criar/editar rascunho não publica anúncio, não envia estoque e não altera `Listing`.
- Importar anúncio existente não sobrescreve automaticamente o rascunho local.

## Interface

- Em Produtos: atalho para fotos e anúncios. Nome e descrição internos, SKU e estoque
  continuam nos seus contextos próprios.
- Em Anúncios: galeria de fotos do produto e lista de rascunhos por produto/canal, com
  seleção/ordem da capa, título, descrição, preço e detalhes comuns. Campos faltantes não
  bloqueiam o salvamento.
- Para Mercado Livre, categoria e atributos são preenchidos conforme a categoria e
  verificados antes do envio. A Shopee poderá ter formulário complementar próprio.

## Segurança e arquivos

- Upload autenticado com permissão de adicionar fotos, limite de tamanho, checagem do
  conteúdo real e tipos aceitos. Arquivos recebem nomes internos aleatórios; nunca confiar
  no nome original para caminho. A API não permite apontar para arquivo de outro produto.
- Arquivo privado enquanto rascunho. Cópias públicas/URLs temporárias só quando exigidas
  pelo canal, sem expor originais ou tokens.
- Exclusão de foto usada em anúncio pede substituição ou desassociação; histórico remoto
  não é apagado por remoção local.

## Entregas incrementais

1. Cadastro e galeria de imagens do produto, rascunhos locais e edição por canal.
2. Validação de regras atuais do Mercado Livre, diagnóstico das fotos e simulação de envio.
3. Publicação explícita no Mercado Livre, vínculo com `Listing` e leitura do retorno.
4. Mapeamento e validação próprios da Shopee quando a integração de anúncios for iniciada.

## Aceite da primeira entrega

- Criar produto sem fotos e anúncio continua válido.
- Subir e ordenar imagens, criar dois rascunhos do mesmo produto e mudar título/preço de um
  não altera o outro nem o cadastro/estoque.
- Só fotos do produto podem ser associadas ao seu rascunho.
- Nenhuma requisição de publicação ou estoque ocorre ao salvar o rascunho.
