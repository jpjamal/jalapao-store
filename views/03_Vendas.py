"""Vendas — Registro de saídas / receitas."""

import streamlit as st
import pandas as pd
from datetime import date
import data_manager as dm

st.header("💰 Registro de Vendas")

# ── Formulário ──────────────────────────────────────────────────────────────
produtos = dm.listar_produtos_ativos()

if not produtos:
    st.warning("Cadastre ao menos um produto antes de registrar vendas.")
    st.stop()

opcoes_produto = {f"{p['sku']} — {p['nome']}": p["id"] for p in produtos}

with st.expander("➕ Nova Venda", expanded=True):
    with st.form("form_venda", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_venda = st.date_input("Data da Venda", value=date.today())
            produto_label = st.selectbox("Produto", list(opcoes_produto.keys()))
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
            preco_venda = st.number_input(
                "Preço de Venda (R$)", min_value=0.01, value=1.00, step=0.01, format="%.2f"
            )

        produto_id = opcoes_produto[produto_label]
        nome_produto = next(p["nome"] for p in produtos if p["id"] == produto_id)
        total = quantidade * preco_venda
        st.markdown(f"**Receita da venda:** R$ {total:,.2f}")

        if st.form_submit_button("💾 Registrar Venda", use_container_width=True):
            dm.inserir("vendas", {
                "data": data_venda.isoformat(),
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_venda": round(preco_venda, 2),
            })
            st.success(f"Venda de **{quantidade}x {nome_produto}** registrada!")
            st.rerun()

# ── Histórico ───────────────────────────────────────────────────────────────
vendas = dm.listar("vendas")

if not vendas:
    st.info("Nenhuma venda registrada ainda.")
    st.stop()

df = pd.DataFrame(vendas)
mapa = dm.mapa_produtos()
df["sku"] = df["produto_id"].map(lambda pid: mapa.get(pid, {}).get("sku", "—"))
df["produto"] = df["produto_id"].map(lambda pid: mapa.get(pid, {}).get("nome", "—"))
df["total"] = df["quantidade"] * df["preco_venda"]
df = df.sort_values("data", ascending=False)

st.subheader(f"Histórico de Vendas ({len(df)})")
st.dataframe(
    df[["id", "data", "sku", "produto", "quantidade", "preco_venda", "total"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "data": "Data",
        "sku": "SKU",
        "produto": "Produto",
        "quantidade": st.column_config.NumberColumn("Qtd"),
        "preco_venda": st.column_config.NumberColumn("Preço Venda", format="R$ %.2f"),
        "total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
    },
)

receita_total = df["total"].sum()
st.metric("Receita Total de Vendas", f"R$ {receita_total:,.2f}")

# ── Remoção ─────────────────────────────────────────────────────────────────
with st.expander("🗑️ Remover venda"):
    ids_vendas = df["id"].tolist()
    del_id = st.selectbox("ID da venda a remover", ids_vendas)
    if st.button("Remover venda", type="primary"):
        dm.remover("vendas", del_id)
        st.success(f"Venda #{del_id} removida.")
        st.rerun()
