"""Dashboard — Resumo financeiro e gráficos."""

import streamlit as st
import pandas as pd
import data_manager as dm

st.header("📊 Dashboard — Jalapão Store")

resumo = dm.resumo_financeiro()
vendas = dm.listar("vendas")
compras = dm.listar("compras")
despesas = dm.listar("despesas")

# ── Métricas principais ────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.metric("🏪 Estoque (Valor)", f"R$ {resumo['total_estoque_valor']:,.2f}")
with col2:
    st.metric("💰 Receita Bruta", f"R$ {resumo['receita_bruta']:,.2f}")

col3, col4 = st.columns(2)

with col3:
    st.metric("📉 Despesas Totais", f"R$ {resumo['despesas_totais']:,.2f}")
with col4:
    cor_lucro = "normal" if resumo["lucro_liquido"] >= 0 else "inverse"
    st.metric(
        "✅ Lucro Líquido",
        f"R$ {resumo['lucro_liquido']:,.2f}",
        delta=f"{'Positivo' if resumo['lucro_liquido'] >= 0 else 'Negativo'}",
        delta_color=cor_lucro,
    )

st.markdown("---")

# ── Detalhamento ────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Composição das Despesas")
    dados_despesa = {
        "Compras (Estoque)": resumo["total_compras"],
        "Despesas Extras": resumo["total_despesas_extras"],
    }
    if any(v > 0 for v in dados_despesa.values()):
        df_desp = pd.DataFrame(
            {"Tipo": dados_despesa.keys(), "Valor": dados_despesa.values()}
        ).set_index("Tipo")
        st.bar_chart(df_desp)
    else:
        st.info("Sem dados de despesas.")

with col_b:
    st.subheader("Receita vs. Custos")
    dados_resultado = {
        "Receita": resumo["receita_bruta"],
        "CMV": resumo["cmv"],
        "Desp. Extras": resumo["total_despesas_extras"],
        "Lucro Líquido": max(resumo["lucro_liquido"], 0),
    }
    if resumo["receita_bruta"] > 0 or resumo["cmv"] > 0:
        df_res = pd.DataFrame(
            {"Categoria": dados_resultado.keys(), "Valor": dados_resultado.values()}
        ).set_index("Categoria")
        st.bar_chart(df_res)
    else:
        st.info("Registre vendas para visualizar.")

st.markdown("---")

# ── Evolução temporal ───────────────────────────────────────────────────────
st.subheader("Evolução Temporal")

tab_vendas, tab_compras = st.tabs(["Vendas por Dia", "Compras por Dia"])

with tab_vendas:
    if vendas:
        df_v = pd.DataFrame(vendas)
        df_v["total"] = df_v["quantidade"] * df_v["preco_venda"]
        vendas_dia = df_v.groupby("data")["total"].sum().sort_index()
        st.line_chart(vendas_dia)
    else:
        st.info("Nenhuma venda registrada.")

with tab_compras:
    if compras:
        df_c = pd.DataFrame(compras)
        df_c["total"] = df_c["quantidade"] * df_c["preco_unitario"]
        compras_dia = df_c.groupby("data")["total"].sum().sort_index()
        st.line_chart(compras_dia)
    else:
        st.info("Nenhuma compra registrada.")

# ── Top produtos ────────────────────────────────────────────────────────────
if vendas:
    st.markdown("---")
    st.subheader("Top Produtos Vendidos")
    df_v = pd.DataFrame(vendas)
    mapa = dm.mapa_produtos()
    df_v["produto"] = df_v["produto_id"].map(lambda pid: mapa.get(pid, {}).get("nome", "—"))
    df_v["total"] = df_v["quantidade"] * df_v["preco_venda"]
    top = df_v.groupby("produto").agg(
        unidades=("quantidade", "sum"),
        receita=("total", "sum"),
    ).sort_values("receita", ascending=False).head(10)
    st.dataframe(
        top.reset_index(),
        use_container_width=True,
        hide_index=True,
        column_config={
            "produto": "Produto",
            "unidades": st.column_config.NumberColumn("Unidades"),
            "receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
        },
    )

# ── Despesas extras por categoria ───────────────────────────────────────────
if despesas:
    st.markdown("---")
    st.subheader("Despesas Extras por Categoria")
    df_d = pd.DataFrame(despesas)
    por_cat = df_d.groupby("categoria")["valor"].sum().sort_values(ascending=False)
    st.bar_chart(por_cat)
