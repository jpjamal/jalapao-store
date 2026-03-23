"""
data_manager — Camada central de persistência JSON.

Todas as operações de leitura/escrita no banco passam por este módulo,
garantindo IDs únicos incrementais e atomicidade nas gravações.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent / "data" / "database.json"

_lock = threading.Lock()

# ── Esquema padrão ──────────────────────────────────────────────────────────

_EMPTY_DB: dict[str, Any] = {
    "produtos": [],
    "compras": [],
    "vendas": [],
    "despesas": [],
    "_counters": {
        "produtos": 0,
        "compras": 0,
        "vendas": 0,
        "despesas": 0,
    },
}


# ── Helpers internos ────────────────────────────────────────────────────────

def _carregar() -> dict[str, Any]:
    """Lê o JSON do disco; cria um vazio se não existir."""
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        _salvar(_EMPTY_DB)
        return json.loads(json.dumps(_EMPTY_DB))
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _salvar(db: dict[str, Any]) -> None:
    """Grava o dicionário inteiro no disco de forma atômica."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_PATH)


def _proximo_id(db: dict, colecao: str) -> int:
    """Retorna e incrementa o contador da coleção."""
    db["_counters"][colecao] = db["_counters"].get(colecao, 0) + 1
    return db["_counters"][colecao]


# ── API pública ─────────────────────────────────────────────────────────────

def listar(colecao: str) -> list[dict]:
    """Retorna todos os registros de uma coleção."""
    with _lock:
        db = _carregar()
    return db.get(colecao, [])


def obter_por_id(colecao: str, registro_id: int) -> dict | None:
    """Busca um registro pelo ID."""
    registros = listar(colecao)
    return next((r for r in registros if r["id"] == registro_id), None)


def inserir(colecao: str, dados: dict) -> dict:
    """Insere um registro com ID auto-incrementado."""
    with _lock:
        db = _carregar()
        dados["id"] = _proximo_id(db, colecao)
        db[colecao].append(dados)
        _salvar(db)
    return dados


def atualizar(colecao: str, registro_id: int, dados: dict) -> bool:
    """Atualiza um registro existente pelo ID."""
    with _lock:
        db = _carregar()
        for i, reg in enumerate(db[colecao]):
            if reg["id"] == registro_id:
                dados["id"] = registro_id
                db[colecao][i] = dados
                _salvar(db)
                return True
    return False


def remover(colecao: str, registro_id: int) -> bool:
    """Remove um registro pelo ID."""
    with _lock:
        db = _carregar()
        tamanho_antes = len(db[colecao])
        db[colecao] = [r for r in db[colecao] if r["id"] != registro_id]
        if len(db[colecao]) < tamanho_antes:
            _salvar(db)
            return True
    return False


def listar_skus() -> list[dict]:
    """Retorna lista simplificada de SKUs ativos para selects."""
    produtos = listar("produtos")
    return [
        {"sku": p["sku"], "nome": p["nome"]}
        for p in produtos
        if p.get("ativo", True)
    ]


def calcular_estoque() -> list[dict]:
    """Calcula saldo de estoque por SKU (compras - vendas)."""
    produtos = {p["sku"]: p for p in listar("produtos")}
    compras = listar("compras")
    vendas = listar("vendas")

    saldo: dict[str, dict] = {}

    for c in compras:
        sku = c["sku"]
        if sku not in saldo:
            info = produtos.get(sku, {})
            saldo[sku] = {
                "sku": sku,
                "produto": info.get("nome", c.get("produto", sku)),
                "categoria": info.get("categoria", "—"),
                "qtd_comprada": 0,
                "qtd_vendida": 0,
                "custo_total": 0.0,
            }
        saldo[sku]["qtd_comprada"] += c["quantidade"]
        saldo[sku]["custo_total"] += c["quantidade"] * c["preco_unitario"]

    for v in vendas:
        sku = v["sku"]
        if sku not in saldo:
            info = produtos.get(sku, {})
            saldo[sku] = {
                "sku": sku,
                "produto": info.get("nome", v.get("produto", sku)),
                "categoria": info.get("categoria", "—"),
                "qtd_comprada": 0,
                "qtd_vendida": 0,
                "custo_total": 0.0,
            }
        saldo[sku]["qtd_vendida"] += v["quantidade"]

    resultado = []
    for item in saldo.values():
        qtd_em_estoque = item["qtd_comprada"] - item["qtd_vendida"]
        custo_medio = (
            item["custo_total"] / item["qtd_comprada"]
            if item["qtd_comprada"] > 0
            else 0.0
        )
        resultado.append({
            "sku": item["sku"],
            "produto": item["produto"],
            "categoria": item["categoria"],
            "qtd_comprada": item["qtd_comprada"],
            "qtd_vendida": item["qtd_vendida"],
            "em_estoque": qtd_em_estoque,
            "custo_medio": round(custo_medio, 2),
            "valor_estoque": round(qtd_em_estoque * custo_medio, 2),
        })

    return sorted(resultado, key=lambda x: x["produto"])


def resumo_financeiro() -> dict:
    """Calcula métricas agregadas para o dashboard."""
    estoque = calcular_estoque()
    vendas = listar("vendas")
    compras = listar("compras")
    despesas = listar("despesas")

    total_estoque_valor = sum(e["valor_estoque"] for e in estoque)
    receita_bruta = sum(v["quantidade"] * v["preco_venda"] for v in vendas)

    # CMV — Custo das Mercadorias Vendidas (custo médio × qtd vendida)
    custo_medio_map = {e["sku"]: e["custo_medio"] for e in estoque}
    cmv = sum(
        v["quantidade"] * custo_medio_map.get(v["sku"], 0)
        for v in vendas
    )

    total_compras = sum(c["quantidade"] * c["preco_unitario"] for c in compras)
    total_despesas_extras = sum(d["valor"] for d in despesas)
    despesas_totais = total_compras + total_despesas_extras

    lucro_liquido = receita_bruta - cmv - total_despesas_extras

    return {
        "total_estoque_valor": round(total_estoque_valor, 2),
        "receita_bruta": round(receita_bruta, 2),
        "cmv": round(cmv, 2),
        "total_compras": round(total_compras, 2),
        "total_despesas_extras": round(total_despesas_extras, 2),
        "despesas_totais": round(despesas_totais, 2),
        "lucro_liquido": round(lucro_liquido, 2),
    }
