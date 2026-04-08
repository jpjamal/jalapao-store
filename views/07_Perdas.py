"""Perdas — Registro de produtos estragados ou devolvidos por defeito."""

import streamlit as st
import pandas as pd
from datetime import date
import data_manager as dm

st.header("📦 Perdas de Produtos")

MOTIVOS_PERDA = [
    "Produto Estragado",
    "Devolução por Defeito",
]

# ── Formulário ──────────────────────────────────────────────────────────────
produtos_ativos = dm.listar_produtos_ativos()

if not produtos_ativos:
    st.warning("Nenhum produto cadastrado. Cadastre produtos primeiro.")
    st.stop()

opcoes_produto = {f"{p['sku']} — {p['nome']}": p["id"] for p in produtos_ativos}

with st.expander("➕ Registrar Perda", expanded=True):
    with st.form("form_perda", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            produto_sel = st.selectbox("Produto", list(opcoes_produto.keys()))
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
        with col2:
            data_perda = st.date_input("Data", value=date.today())
            motivo = st.selectbox("Motivo", MOTIVOS_PERDA)

        observacao = st.text_input("Observação (opcional)")

        if st.form_submit_button("💾 Registrar Perda", use_container_width=True):
            produto_id = opcoes_produto[produto_sel]
            dm.inserir("perdas", {
                "produto_id": produto_id,
                "quantidade": quantidade,
                "motivo": motivo,
                "observacao": observacao.strip(),
                "data": data_perda.isoformat(),
            })
            st.success(
                f"Perda registrada: **{quantidade}x** {produto_sel} — {motivo}"
            )
            st.rerun()

# ── Histórico ───────────────────────────────────────────────────────────────
perdas = dm.listar("perdas")

if not perdas:
    st.info("Nenhuma perda registrada.")
    st.stop()

df = pd.DataFrame(perdas)
mapa = dm.mapa_produtos()
df["produto"] = df["produto_id"].map(lambda pid: mapa.get(pid, {}).get("nome", "—"))
df = df.sort_values("data", ascending=False)

# Calcular valor da perda usando custo médio
estoque = dm.calcular_estoque()
custo_medio_map = {e["produto_id"]: e["custo_medio"] for e in estoque}
df["valor_perda"] = df.apply(
    lambda r: round(r["quantidade"] * custo_medio_map.get(r["produto_id"], 0), 2),
    axis=1,
)

st.subheader(f"Histórico de Perdas ({len(df)})")
st.dataframe(
    df[["id", "data", "produto", "quantidade", "motivo", "observacao", "valor_perda"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "data": "Data",
        "produto": "Produto",
        "quantidade": st.column_config.NumberColumn("Qtd"),
        "motivo": "Motivo",
        "observacao": "Observação",
        "valor_perda": st.column_config.NumberColumn("Valor Perda", format="R$ %.2f"),
    },
)

st.metric("Total de Perdas", f"R$ {df['valor_perda'].sum():,.2f}")

# ── Remoção ─────────────────────────────────────────────────────────────────
with st.expander("🗑️ Remover perda"):
    ids_perdas = df["id"].tolist()
    del_id = st.selectbox("ID da perda a remover", ids_perdas)
    if st.button("Remover perda", type="primary"):
        dm.remover("perdas", del_id)
        st.success(f"Perda #{del_id} removida.")
        st.rerun()
