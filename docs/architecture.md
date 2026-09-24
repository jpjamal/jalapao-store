# Arquitetura e modelo de dados

```mermaid
flowchart LR
  Browser[Navegador] -->|HTTPS 443| Traefik[Traefik compartilhado]
  Traefik -->|HTTP 8080 na rede Docker| Proxy[Nginx interno da loja]
  Proxy --> Next[Next.js / BFF]
  Next -->|JWT interno| API[Django REST Framework]
  Proxy --> Admin[Django Admin]
  API --> DB[(PostgreSQL exclusivo)]
  Admin --> DB
  Traefik -->|ACME HTTP-01| DomainCert[Certificado do domínio]
  Certbot[Certbot: certificado do IP] --> Certs[Volume de certificados]
  Certs --> Traefik
```

O Traefik compartilhado atende as portas públicas 80 e 443 e termina o HTTPS. O Nginx
da Jalapão não publica porta no host: recebe HTTP do Traefik, encaminha as rotas da
aplicação, do Admin e da API, serve os manuais em PDF e o desafio ACME do certificado
por IP. O certificado do domínio `jpsys.duckdns.org` é emitido pelo Traefik; o do IP
continua sendo renovado pelo Certbot e servido pelo Traefik. Banco e API não publicam
portas no host. Código, segredos e dados têm ciclos separados.

```mermaid
erDiagram
  User ||--o{ Sale : registra
  User ||--o{ Movement : movimenta
  User ||--o{ CashEntry : registra
  Product ||--o| PrintingProfile : parametros_3d
  Product ||--|| Stock : saldo
  Product ||--o{ Movement : historico
  Product ||--o{ SaleItem : vendido_em
  Product ||--o{ Listing : anuncio_externo
  Sale ||--|{ SaleItem : contem
  Sale ||--o{ Movement : baixa_ou_estorna
  Sale ||--o{ CashEntry : recebe_ou_estorna
```

As entidades comerciais usam UUID; os usuários mantêm PK padrão Django. IDs externos
permanecem em campos próprios. FKs de histórico usam PROTECT; perfis 3D são dependentes
do produto. A quantidade atual é uma projeção mantida junto do razão de movimentos.
OutboxEvent recebe intenção de sincronização na mesma transação; ainda não há worker externo.

Apps não são microsserviços: uma transação PostgreSQL mantém a consistência entre venda,
estoque e caixa. Cálculo puro em domain.py; casos de uso em services.py; serialização e
permissões em api.py. ORM e migrations seguem convenções Django, sem repositórios artificiais.

## Valores gerenciais
| Indicador | Regra |
|---|---|
| Estoque em reais | Valor persistido das entradas menos saídas pelo custo médio móvel |
| Faturamento | Bruto das vendas confirmadas, inclusive ainda não recebidas |
| Líquido da venda | Bruto − desconto − taxas − frete pago pela loja |
| Lucro estimado | Líquido − custo dos itens congelado na venda |
| A receber | Líquido das vendas confirmadas não recebidas |
| Caixa | Entradas efetivas − saídas efetivas, incluindo estornos |

Fluxo de caixa manual não altera automaticamente lucro de vendas. Compra/produção de
estoque é registrada como entrada e movimento; pagar uma compra gera saída de caixa uma vez.
O operador informa taxas efetivas; calculadoras antigas continuam sendo simulações.
