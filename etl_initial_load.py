"""
ETL — Carga inicial dos CSVs para o banco JSON.

Lê produtos.csv, compras.csv e vendas.csv, normaliza os dados e gera
o arquivo data/database.json com a estrutura esperada pelo data_manager.
"""

import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CSV_DIR = Path(__file__).parent / "csv_source"

CATEGORIAS_NORMALIZADAS = {
    "eletronicos": "Eletrônicos",
    "joias e acessórios": "Joias e Acessórios",
}


def _normalizar_categoria(cat: str) -> str:
    return CATEGORIAS_NORMALIZADAS.get(cat.strip().lower(), cat.strip().title())


def _converter_data(data_br: str) -> str:
    """Converte DD/MM/YYYY → YYYY-MM-DD. Se já estiver em ISO, retorna como está."""
    data_br = data_br.strip()
    if "-" in data_br and len(data_br) == 10 and data_br[4] == "-":
        return data_br
    partes = data_br.split("/")
    if len(partes) == 3:
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return data_br


def _ler_csv(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def _gerar_descricao(nome: str, categoria: str) -> str:
    return f"{nome.strip()} — Categoria: {categoria}"


def carregar_produtos(caminho: Path) -> list[dict]:
    rows = _ler_csv(caminho)
    produtos = []
    for idx, row in enumerate(rows, start=1):
        sku = row.get("sku") or row.get("SKU", "")
        nome = row.get("nome_do_produto") or row.get("Nome do Produto", "")
        categoria_raw = row.get("categoria") or row.get("Categoria", "Geral")
        ativo_raw = row.get("ativo") or row.get("Ativo", "Sim")

        categoria = _normalizar_categoria(categoria_raw)
        produtos.append({
            "id": idx,
            "sku": sku.strip().upper(),
            "nome": nome.strip(),
            "descricao": _gerar_descricao(nome, categoria),
            "categoria": categoria,
            "ativo": ativo_raw.strip().lower().startswith("sim"),
        })
    return produtos


def _montar_mapa_sku_id(produtos: list[dict]) -> dict[str, int]:
    """Cria mapa SKU → produto_id para lookup nas compras/vendas."""
    return {p["sku"]: p["id"] for p in produtos}


def _montar_mapa_nome_id(produtos: list[dict]) -> dict[str, int]:
    """Cria mapa nome_normalizado → produto_id para lookup nas compras/vendas."""
    mapa = {}
    for p in produtos:
        chave = p["nome"].strip().lower()
        mapa[chave] = p["id"]
    return mapa


def _resolver_produto_id(nome_produto: str, mapa_nome: dict[str, int]) -> int | None:
    """Tenta encontrar o produto_id pelo nome do produto."""
    chave = nome_produto.strip().lower()
    if chave in mapa_nome:
        return mapa_nome[chave]
    for nome_cadastrado, pid in mapa_nome.items():
        if chave in nome_cadastrado or nome_cadastrado in chave:
            return pid
    return None


def carregar_compras(
    caminho: Path, mapa_sku_id: dict[str, int], mapa_nome_id: dict[str, int], proximo_id: int = 1
) -> list[dict]:
    rows = _ler_csv(caminho)
    compras = []
    for idx, row in enumerate(rows, start=proximo_id):
        nome = (row.get("produto") or row.get("Produto", "")).strip()
        sku = (row.get("sku") or row.get("SKU", "")).strip().upper()
        data_raw = row.get("data") or row.get("Data", "")
        quantidade = int(row.get("quantidade") or row.get("Quantidade", "0"))
        preco_raw = (
            row.get("custo_unit_final")
            or row.get("Custo_Unit_Final")
            or row.get("preco_unitario")
            or "0"
        )

        produto_id = mapa_sku_id.get(sku) if sku else None
        if produto_id is None:
            produto_id = _resolver_produto_id(nome, mapa_nome_id)

        compras.append({
            "id": idx,
            "data": _converter_data(data_raw),
            "produto_id": produto_id,
            "quantidade": quantidade,
            "preco_unitario": round(float(preco_raw.strip()), 2),
        })
    return compras


def carregar_vendas(
    caminho: Path, mapa_sku_id: dict[str, int], mapa_nome_id: dict[str, int], proximo_id: int = 1
) -> list[dict]:
    rows = _ler_csv(caminho)
    vendas = []
    for idx, row in enumerate(rows, start=proximo_id):
        nome = (row.get("produto") or row.get("Produto", "")).strip()
        sku = (row.get("sku") or row.get("SKU", "")).strip().upper()
        data_raw = row.get("data") or row.get("Data", "")
        quantidade = int(row.get("quantidade") or row.get("Quantidade", "0"))
        preco_raw = (
            row.get("preco_venda")
            or row.get("Preco_Venda")
            or "0"
        )

        produto_id = mapa_sku_id.get(sku) if sku else None
        if produto_id is None:
            produto_id = _resolver_produto_id(nome, mapa_nome_id)

        vendas.append({
            "id": idx,
            "data": _converter_data(data_raw),
            "produto_id": produto_id,
            "quantidade": quantidade,
            "preco_venda": round(float(preco_raw.strip()), 2),
        })
    return vendas


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    produtos_path = CSV_DIR / "produtos.csv"
    compras_path = CSV_DIR / "compras.csv"
    vendas_path = CSV_DIR / "vendas.csv"

    # 1) Produtos
    produtos = carregar_produtos(produtos_path) if produtos_path.exists() else []
    mapa_sku_id = _montar_mapa_sku_id(produtos)
    mapa_nome_id = _montar_mapa_nome_id(produtos)

    # 2) Compras
    compras = (
        carregar_compras(compras_path, mapa_sku_id, mapa_nome_id)
        if compras_path.exists()
        else []
    )

    # 3) Vendas
    vendas = (
        carregar_vendas(vendas_path, mapa_sku_id, mapa_nome_id)
        if vendas_path.exists() and vendas_path.stat().st_size > 0
        else []
    )

    database = {
        "produtos": produtos,
        "compras": compras,
        "vendas": vendas,
        "despesas": [],
        "_counters": {
            "produtos": len(produtos),
            "compras": len(compras),
            "vendas": len(vendas),
            "despesas": 0,
        },
    }

    db_path = DATA_DIR / "database.json"
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Banco gerado em {db_path}")
    print(f"   Produtos: {len(produtos)}")
    print(f"   Compras:  {len(compras)}")
    print(f"   Vendas:   {len(vendas)}")

    # Verificação de produtos não resolvidos
    sem_produto = [
        c for c in compras if c["produto_id"] is None
    ] + [v for v in vendas if v["produto_id"] is None]
    if sem_produto:
        print(f"   ⚠️  {len(sem_produto)} registro(s) com produto não resolvido")


if __name__ == "__main__":
    main()
