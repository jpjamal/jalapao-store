# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jalapão Store is a cash flow and inventory management system for a small import business. Built with Python 3.11, Streamlit, and JSON file-based persistence. The UI and all business logic are in Portuguese (pt-BR).

## Commands

```bash
# Run with Docker (preferred)
docker compose up --build
# Access at http://localhost:8501

# Run locally (without Docker)
pip install -r requirements.txt
streamlit run app.py
```

There are no tests or linting configured.

## Architecture

- **`app.py`** — Streamlit entrypoint. Sets page config, sidebar, and displays summary metrics from `data_manager.get_resumo()`.
- **`data_manager.py`** — Single module for all persistence and business logic. Reads/writes a JSON file (`data/db.json`). On first run, copies `data/seed_data.json` as the initial database. All CRUD operations (produtos, compras, vendas, despesas) and computed views (estoque, resumo) live here.
- **`pages/`** — Streamlit multi-page app. Each page imports `data_manager` via `sys.path.insert` to the parent directory. Pages are numbered 01-06 and cover: product CRUD, purchases, sales, extra expenses, inventory view, and financial dashboard.

### Data Model (all stored in `data/db.json`)

The JSON database has four top-level arrays: `produtos`, `compras`, `vendas`, `despesas`. Products are keyed by `sku` (string). Compras/vendas/despesas use auto-incrementing integer `id`.

Inventory (`estoque`) is not stored — it is computed on the fly as `compras - vendas` per SKU, with weighted average cost.

### Financial Logic

```
Lucro Líquido = Receita de Vendas − CMV (custo médio × qtd vendida) − Despesas Extras
```

The README documents import tax rules (Remessa Conforme) and platform fee structures (Shopee, ML, OLX) that are part of the business context but not yet implemented in code.

## Key Conventions

- Data directory is configurable via `DATA_DIR` env var (defaults to `./data/`). Docker sets it to `/app/data` with a named volume for persistence.
- All monetary values are rounded to 2 decimal places and displayed in BRL (R$).
- Pages import `data_manager` using `sys.path.insert(0, str(Path(__file__).parent.parent))` — maintain this pattern when adding new pages.
