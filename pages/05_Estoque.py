"""Estoque — Tabela dinâmica de saldo atual por SKU."""

import streamlit as st
import pandas as pd
import data_manager as dm

st.header("📋 Controle de Estoque")

estoque = dm.calcular_estoque()

if not estoque:
    st.info("Nenhum dado de estoque disponível. Registre compras primeiro.")
    st.stop()

df = pd.DataFrame(estoque)

# ── Filtros ─────────────────────────────────────────────────────────────────
col_filtro1, col_filtro2 = st.columns(2)
with col_filtro1:
    categorias = ["Todas"] + sorted(df["categoria"].unique().tolist())
    cat_sel = st.selectbox("Filtrar por categoria", categorias)
with col_filtro2:
    apenas_com_estoque = st.checkbox("Apenas itens em estoque", value=False)

if cat_sel != "Todas":
    df = df[df["categoria"] == cat_sel]
if apenas_com_estoque:
    df = df[df["em_estoque"] > 0]

# ── Tabela ──────────────────────────────────────────────────────────────────
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "sku": "SKU",
        "produto": "Produto",
        "categoria": "Categoria",
        "qtd_comprada": st.column_config.NumberColumn("Comprado"),
        "qtd_vendida": st.column_config.NumberColumn("Vendido"),
        "em_estoque": st.column_config.NumberColumn("Em Estoque"),
        "custo_medio": st.column_config.NumberColumn("Custo Médio", format="R$ %.2f"),
        "valor_estoque": st.column_config.NumberColumn("Valor Estoque", format="R$ %.2f"),
    },
)

# ── Métricas ────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Itens Distintos", len(df))
with col2:
    st.metric("Unidades em Estoque", int(df["em_estoque"].sum()))
with col3:
    st.metric("Valor Total do Estoque", f"R$ {df['valor_estoque'].sum():,.2f}")

# ── Alerta de estoque baixo ────────────────────────────────────────────────
baixo_estoque = df[df["em_estoque"] <= 0]
if not baixo_estoque.empty:
    st.warning(
        f"⚠️ {len(baixo_estoque)} produto(s) com estoque zerado ou negativo: "
        + ", ".join(baixo_estoque["produto"].tolist())
    )
