"""
app.py — Entrypoint da aplicação Jalapão Store.

Configura o tema, sidebar e navegação multipage do Streamlit.
"""

import streamlit as st

st.set_page_config(
    page_title="Jalapão Store — Gestão",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Conteúdo principal — largura total */
    .stMainBlockContainer, [data-testid="stAppViewBlockContainer"] {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* Métricas */
    [data-testid="stMetric"] {
        background: var(--background-secondary, #f8f9fa);
        border-radius: .75rem;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(128,128,128,.15);
    }
    /* Botões de ação */
    .stButton > button {
        border-radius: .5rem;
    }
    /* Tabs mais espaçadas */
    .stTabs [data-baseweb="tab-list"] { gap: .5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Navegação ───────────────────────────────────────────────────────────────
paginas = st.navigation(
    [
        st.Page("views/06_Dashboard.py",       title="Dashboard",       icon="📊", default=True),
        st.Page("views/01_Cadastro_Produtos.py", title="Produtos",       icon="📦"),
        st.Page("views/02_Compras.py",          title="Compras",         icon="🛒"),
        st.Page("views/03_Vendas.py",           title="Vendas",          icon="💰"),
        st.Page("views/04_Despesas_Extras.py",  title="Despesas Extras", icon="💸"),
        st.Page("views/05_Estoque.py",          title="Estoque",         icon="📋"),
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("🌶️ Jalapão Store · v1.0")

paginas.run()
