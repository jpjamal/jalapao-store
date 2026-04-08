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
    "perdas": [],
    "_counters": {
        "produtos": 0,
        "compras": 0,
        "vendas": 0,
        "despesas": 0,
        "perdas": 0,
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
        db = json.load(f)
    # Migra coleções novas que ainda não existem no arquivo
    atualizado = False
    for chave, valor in _EMPTY_DB.items():
        if chave == "_counters":
            for k, v in valor.items():
                if k not in db.get("_counters", {}):
                    db.setdefault("_counters", {})[k] = v
                    atualizado = True
        elif chave not in db:
            db[chave] = valor
            atualizado = True
    if atualizado:
        _salvar(db)
    return db


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


def listar_produtos_ativos() -> list[dict]:
    """Retorna lista de produtos ativos para selects (id, sku, nome)."""
    produtos = listar("produtos")
    return [
        {"id": p["id"], "sku": p["sku"], "nome": p["nome"]}
        for p in produtos
        if p.get("ativo", True)
    ]


def mapa_produtos() -> dict[int, dict]:
    """Retorna dicionário {id: {sku, nome, categoria}} de todos os produtos."""
    return {
        p["id"]: {"sku": p["sku"], "nome": p["nome"], "categoria": p.get("categoria", "—")}
        for p in listar("produtos")
    }


def calcular_estoque() -> list[dict]:
    """Calcula saldo de estoque por produto_id (compras - vendas - perdas)."""
    produtos = mapa_produtos()
    compras = listar("compras")
    vendas = listar("vendas")
    perdas = listar("perdas")

    saldo: dict[int, dict] = {}

    def _garantir_produto(pid: int) -> None:
        if pid not in saldo:
            info = produtos.get(pid, {})
            saldo[pid] = {
                "produto_id": pid,
                "sku": info.get("sku", "—"),
                "produto": info.get("nome", "—"),
                "categoria": info.get("categoria", "—"),
                "qtd_comprada": 0,
                "qtd_vendida": 0,
                "qtd_perdida": 0,
                "custo_total": 0.0,
            }

    for c in compras:
        pid = c["produto_id"]
        _garantir_produto(pid)
        saldo[pid]["qtd_comprada"] += c["quantidade"]
        saldo[pid]["custo_total"] += c["quantidade"] * c["preco_unitario"]

    for v in vendas:
        pid = v["produto_id"]
        _garantir_produto(pid)
        saldo[pid]["qtd_vendida"] += v["quantidade"]

    for p in perdas:
        pid = p["produto_id"]
        _garantir_produto(pid)
        saldo[pid]["qtd_perdida"] += p["quantidade"]

    resultado = []
    for item in saldo.values():
        qtd_em_estoque = item["qtd_comprada"] - item["qtd_vendida"] - item["qtd_perdida"]
        custo_medio = (
            item["custo_total"] / item["qtd_comprada"]
            if item["qtd_comprada"] > 0
            else 0.0
        )
        resultado.append({
            "produto_id": item["produto_id"],
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
    perdas = listar("perdas")

    total_estoque_valor = sum(e["valor_estoque"] for e in estoque)
    receita_bruta = sum(v["quantidade"] * v["preco_venda"] for v in vendas)

    # CMV — Custo das Mercadorias Vendidas (custo médio × qtd vendida)
    custo_medio_map = {e["produto_id"]: e["custo_medio"] for e in estoque}
    cmv = sum(
        v["quantidade"] * custo_medio_map.get(v["produto_id"], 0)
        for v in vendas
    )

    # Perdas — custo médio × qtd perdida
    total_perdas = sum(
        p["quantidade"] * custo_medio_map.get(p["produto_id"], 0)
        for p in perdas
    )

    total_compras = sum(c["quantidade"] * c["preco_unitario"] for c in compras)
    total_despesas_extras = sum(d["valor"] for d in despesas)
    despesas_totais = total_compras + total_despesas_extras + total_perdas

    lucro_liquido = receita_bruta - cmv - total_despesas_extras - total_perdas

    return {
        "total_estoque_valor": round(total_estoque_valor, 2),
        "receita_bruta": round(receita_bruta, 2),
        "cmv": round(cmv, 2),
        "total_compras": round(total_compras, 2),
        "total_despesas_extras": round(total_despesas_extras, 2),
        "total_perdas": round(total_perdas, 2),
        "despesas_totais": round(despesas_totais, 2),
        "lucro_liquido": round(lucro_liquido, 2),
    }
