"""Compras — Registro de entradas de estoque (despesa de itens)."""

import streamlit as st
import pandas as pd
from datetime import date
import data_manager as dm

st.header("🛒 Registro de Compras")

# ── Formulário ──────────────────────────────────────────────────────────────
skus = dm.listar_skus()

if not skus:
    st.warning("Cadastre ao menos um produto antes de registrar compras.")
    st.stop()

opcoes_produto = {f"{s['sku']} — {s['nome']}": s["sku"] for s in skus}

with st.expander("➕ Nova Compra", expanded=True):
    with st.form("form_compra", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_compra = st.date_input("Data da Compra", value=date.today())
            produto_label = st.selectbox("Produto", list(opcoes_produto.keys()))
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
            preco_unitario = st.number_input(
                "Preço Unitário (R$)", min_value=0.01, value=1.00, step=0.01, format="%.2f"
            )

        sku_selecionado = opcoes_produto[produto_label]
        nome_produto = next(s["nome"] for s in skus if s["sku"] == sku_selecionado)
        total = quantidade * preco_unitario
        st.markdown(f"**Total da compra:** R$ {total:,.2f}")

        if st.form_submit_button("💾 Registrar Compra", use_container_width=True):
            dm.inserir("compras", {
                "data": data_compra.isoformat(),
                "sku": sku_selecionado,
                "produto": nome_produto,
                "quantidade": quantidade,
                "preco_unitario": round(preco_unitario, 2),
            })
            st.success(f"Compra de **{quantidade}x {nome_produto}** registrada!")
            st.rerun()

# ── Histórico ───────────────────────────────────────────────────────────────
compras = dm.listar("compras")

if not compras:
    st.info("Nenhuma compra registrada.")
    st.stop()

df = pd.DataFrame(compras)
df["total"] = df["quantidade"] * df["preco_unitario"]
df = df.sort_values("data", ascending=False)

st.subheader(f"Histórico de Compras ({len(df)})")
st.dataframe(
    df[["id", "data", "sku", "produto", "quantidade", "preco_unitario", "total"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "data": "Data",
        "sku": "SKU",
        "produto": "Produto",
        "quantidade": st.column_config.NumberColumn("Qtd"),
        "preco_unitario": st.column_config.NumberColumn("Preço Unit.", format="R$ %.2f"),
        "total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
    },
)

total_compras = df["total"].sum()
st.metric("Total Investido em Compras", f"R$ {total_compras:,.2f}")

# ── Remoção ─────────────────────────────────────────────────────────────────
with st.expander("🗑️ Remover compra"):
    ids_compras = df["id"].tolist()
    del_id = st.selectbox("ID da compra a remover", ids_compras)
    if st.button("Remover compra", type="primary"):
        dm.remover("compras", del_id)
        st.success(f"Compra #{del_id} removida.")
        st.rerun()
