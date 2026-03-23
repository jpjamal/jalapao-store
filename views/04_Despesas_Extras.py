"""Despesas Extras — Marketing, Taxas de Entrega, Embalagens, Custos Fixos."""

import streamlit as st
import pandas as pd
from datetime import date
import data_manager as dm

st.header("💸 Despesas Operacionais")

CATEGORIAS_DESPESA = [
    "Anúncios Facebook/Ads",
    "Anúncios Mercado Livre",
    "Taxa de Entrega",
    "Embalagens",
    "Taxa Marketplace",
    "Frete Importação",
    "Custos Fixos",
    "Outros",
]

# ── Formulário ──────────────────────────────────────────────────────────────
with st.expander("➕ Nova Despesa", expanded=True):
    with st.form("form_despesa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_despesa = st.date_input("Data", value=date.today())
            categoria = st.selectbox("Categoria", CATEGORIAS_DESPESA)
        with col2:
            descricao = st.text_input("Descrição")
            valor = st.number_input(
                "Valor (R$)", min_value=0.01, value=1.00, step=0.01, format="%.2f"
            )

        if st.form_submit_button("💾 Registrar Despesa", use_container_width=True):
            dm.inserir("despesas", {
                "data": data_despesa.isoformat(),
                "categoria": categoria,
                "descricao": descricao.strip() or categoria,
                "valor": round(valor, 2),
            })
            st.success(f"Despesa de **R$ {valor:,.2f}** ({categoria}) registrada!")
            st.rerun()

# ── Histórico ───────────────────────────────────────────────────────────────
despesas = dm.listar("despesas")

if not despesas:
    st.info("Nenhuma despesa extra registrada.")
    st.stop()

df = pd.DataFrame(despesas)
df = df.sort_values("data", ascending=False)

st.subheader(f"Histórico de Despesas ({len(df)})")
st.dataframe(
    df[["id", "data", "categoria", "descricao", "valor"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "data": "Data",
        "categoria": "Categoria",
        "descricao": "Descrição",
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)

# ── Resumo por categoria ───────────────────────────────────────────────────
st.subheader("Resumo por Categoria")
resumo = df.groupby("categoria")["valor"].sum().sort_values(ascending=False)
col1, col2 = st.columns([1, 1])
with col1:
    st.dataframe(
        resumo.reset_index().rename(columns={"categoria": "Categoria", "valor": "Total (R$)"}),
        use_container_width=True,
        hide_index=True,
    )
with col2:
    st.bar_chart(resumo, horizontal=True)

st.metric("Total de Despesas Extras", f"R$ {df['valor'].sum():,.2f}")

# ── Remoção ─────────────────────────────────────────────────────────────────
with st.expander("🗑️ Remover despesa"):
    ids_despesas = df["id"].tolist()
    del_id = st.selectbox("ID da despesa a remover", ids_despesas)
    if st.button("Remover despesa", type="primary"):
        dm.remover("despesas", del_id)
        st.success(f"Despesa #{del_id} removida.")
        st.rerun()
