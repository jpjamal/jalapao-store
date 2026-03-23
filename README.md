# 🌶️ Jalapão Store — Sistema de Fluxo de Caixa e Estoque

Sistema completo de gestão para micro-comércio, desenvolvido em **Python/Streamlit** com persistência em JSON e conteinerização Docker.

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Dashboard** | Métricas financeiras (estoque, receita, despesas, lucro líquido) e gráficos |
| **Produtos** | CRUD completo de itens com SKU, categoria e status |
| **Compras** | Registro de entradas de estoque (despesas com mercadoria) |
| **Vendas** | Registro de saídas / receitas |
| **Despesas Extras** | Marketing, taxas, embalagens, custos fixos |
| **Estoque** | Tabela dinâmica com saldo, custo médio e valor em estoque |

## Início Rápido

### Com Docker (recomendado)

```bash
docker compose up --build -d
```

Acesse: **http://localhost:8501**

### Sem Docker

```bash
pip install -r requirements.txt
python etl_initial_load.py   # Carga inicial dos CSVs
streamlit run app.py
```

## Estrutura do Projeto

```
jalapao-store/
├── app.py                    # Entrypoint e navegação
├── data_manager.py           # Camada de persistência JSON
├── etl_initial_load.py       # ETL — carga inicial dos CSVs
├── views/
│   ├── 01_Cadastro_Produtos.py
│   ├── 02_Compras.py
│   ├── 03_Vendas.py
│   ├── 04_Despesas_Extras.py
│   ├── 05_Estoque.py
│   └── 06_Dashboard.py
├── csv_source/               # CSVs originais para carga inicial
├── data/                     # database.json (gerado pelo ETL)
├── .streamlit/config.toml    # Tema e configuração
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Lógica de Negócio

- **Lucro Líquido** = Receita de Vendas − CMV − Despesas Extras
- **CMV** = Σ (quantidade vendida × custo médio do SKU)
- **Custo Médio** = Σ custo total das compras / Σ quantidade comprada (por SKU)
- **Valor em Estoque** = quantidade em estoque × custo médio

## Persistência

Os dados são armazenados em `data/database.json` com IDs numéricos auto-incrementais. O volume Docker garante que os dados sobrevivam a reinicializações do container.
