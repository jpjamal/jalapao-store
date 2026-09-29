# Specs

Uma pasta por mudança: `spec.md` (o quê e por quê) → `plan.md` (como) → `tasks.md` (o que
foi feito e o que falta) → `validation.md` (evidência). Regras em
[constituição](../constitution.md); a organização do código atual em
[arquitetura](../architecture.md). Specs antigas citam os caminhos de código da época.

| Spec | Assunto | Pendente |
|---|---|---|
| [001](001-platform/spec.md) | Gestão Jalapão Store — regras gerais, contrato do backend e critérios da interface | — |
| [002](002-stock-cost/spec.md) | Compras, produção e custo médio do estoque | — |
| [003](003-ferramentas-no-app/spec.md) | Ferramentas no app e aviso de certificado | — |
| [004](004-busca-de-produto/spec.md) | Busca de produto por digitação | — |
| [005](005-integracao-marketplaces/spec.md) | Integração com marketplaces (Shopee primeiro) | primeira conexão real da Shopee |
| [006](006-mercado-livre/spec.md) | Mercado Livre: conexão | — |
| [007](007-tokens-e-entrega-estoque/spec.md) | Tokens protegidos e entrega de estoque por anúncio | — |
| [008](008-dominio-jpsys/spec.md) | Domínio jpsys.duckdns.org | retorno nos painéis do Mercado Livre e da Shopee |
| [009](009-rascunhos-anuncios/spec.md) | Fotos do produto e rascunhos de anúncio | atributos e publicação da Shopee |
| [010](010-sku-automatico/spec.md) | SKU automático | — |
| [011](011-validacao-anuncio-ml/spec.md) | Validar o rascunho no Mercado Livre | — |
| [012](012-publicacao-ml/spec.md) | Publicar e editar anúncio no Mercado Livre | — |
| [013](013-pesquisa-precos-ml/spec.md) | Pesquisa de mercado no Mercado Livre | — |
| [014](014-app-instalavel/spec.md) | App instalável (PWA) com o ícone da marca | instalar no Android e conferir |
| [015](015-vendas-marketplace/spec.md) | Canais da venda e importação de vendas do Mercado Livre | primeira venda real; Shopee |
| [016](016-padronizar-sku/spec.md) | Padronizar o SKU dos produtos antigos | — |
| [017](017-reestruturacao-ddd/spec.md) | Reestruturação do código por contexto (DDD) | conferir as telas com login |
| [018](018-https-no-traefik/spec.md) | HTTPS no Traefik (antes numerada 007) | certificados órfãos |
| [019](019-traefik-unico/spec.md) | Traefik como único proxy (sem Nginx; Certbot central) | apagar o volume antigo de certificados |
| [020](020-servidor-de-arquivos/spec.md) | Servidor de arquivos (SILO): fotos e manuais em buckets | — |
| [021](021-codigo-de-barras/spec.md) | Código de barras (GTIN/EAN) opcional no produto | conferir com leitor de verdade; enviar GTIN aos marketplaces |
| [022](022-categorias-e-dados-do-produto/spec.md) | Categorias no lugar do tipo; marca, modelo e peso do produto | conferir as telas com login |

Próxima spec: **023**.
