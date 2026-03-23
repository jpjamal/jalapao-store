"""Cadastro de Produtos — CRUD completo."""

import streamlit as st
import pandas as pd
import data_manager as dm

st.header("📦 Cadastro de Produtos")

# ── Formulário de cadastro ──────────────────────────────────────────────────
with st.expander("➕ Novo Produto", expanded=False):
    with st.form("form_produto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Produto*")
            categoria = st.selectbox(
                "Categoria",
                ["Eletrônicos", "Joias e Acessórios", "Acessórios", "Outros"],
            )
        with col2:
            sku = st.text_input("SKU*", help="Código único do produto")
            descricao = st.text_input("Descrição breve")

        if st.form_submit_button("💾 Salvar", use_container_width=True):
            if not nome or not sku:
                st.error("Nome e SKU são obrigatórios.")
            else:
                dm.inserir("produtos", {
                    "sku": sku.strip().upper(),
                    "nome": nome.strip(),
                    "descricao": descricao.strip() or f"{nome.strip()} — {categoria}",
                    "categoria": categoria,
                    "ativo": True,
                })
                st.success(f"Produto **{nome}** cadastrado!")
                st.rerun()

# ── Listagem ────────────────────────────────────────────────────────────────
produtos = dm.listar("produtos")

if not produtos:
    st.info("Nenhum produto cadastrado ainda.")
    st.stop()

df = pd.DataFrame(produtos)
colunas_exibidas = ["id", "sku", "nome", "categoria", "ativo"]
colunas_presentes = [c for c in colunas_exibidas if c in df.columns]

st.subheader(f"Produtos cadastrados ({len(df)})")
st.dataframe(
    df[colunas_presentes],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "sku": "SKU",
        "nome": "Nome",
        "categoria": "Categoria",
        "ativo": st.column_config.CheckboxColumn("Ativo"),
    },
)

# ── Edição / Exclusão ──────────────────────────────────────────────────────
st.subheader("Editar / Remover")

ids_disponiveis = [p["id"] for p in produtos]
produto_id = int(st.selectbox("Selecione o ID do produto", ids_disponiveis))
produto_sel = dm.obter_por_id("produtos", produto_id)

if produto_sel:
    tab_edit, tab_del = st.tabs(["✏️ Editar", "🗑️ Remover"])

    with tab_edit:
        with st.form("form_editar_produto"):
            col1, col2 = st.columns(2)
            with col1:
                e_nome = st.text_input("Nome", value=produto_sel["nome"])
                e_categoria = st.text_input("Categoria", value=produto_sel.get("categoria", ""))
            with col2:
                e_sku = st.text_input("SKU", value=produto_sel["sku"])
                e_desc = st.text_input("Descrição", value=produto_sel.get("descricao", ""))
            e_ativo = st.checkbox("Ativo", value=produto_sel.get("ativo", True))

            if st.form_submit_button("Atualizar", use_container_width=True):
                dm.atualizar("produtos", produto_id, {
                    "sku": e_sku.strip().upper(),
                    "nome": e_nome.strip(),
                    "descricao": e_desc.strip(),
                    "categoria": e_categoria.strip(),
                    "ativo": e_ativo,
                })
                st.success("Produto atualizado!")
                st.rerun()

    with tab_del:
        st.warning(f"Deseja remover **{produto_sel['nome']}** (ID {produto_id})?")
        if st.button("Confirmar exclusão", type="primary"):
            dm.remover("produtos", produto_id)
            st.success("Produto removido.")
            st.rerun()
