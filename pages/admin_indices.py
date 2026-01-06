import streamlit as st
import time
from utils.db import get_market_indices, get_supabase_client

def show_admin_indices():
    st.title("📈 Admin: Índices de Mercado")
    
    # 1. CONEXÃO
    try:
        supabase = get_supabase_client()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return

    # === ÁREA DE CRIAÇÃO (Com Limpeza Automática) ===
    with st.expander("➕ Adicionar Novo Índice", expanded=False):
        c_new1, c_new2, c_new3 = st.columns([3, 2, 1])
        
        with c_new1:
            # Adicionei a key="new_name_input" para podermos limpar depois
            new_idx_name = st.text_input(
                "Nome", 
                placeholder="Ex: IGPM", 
                label_visibility="collapsed",
                key="new_name_input" 
            )
        
        with c_new2:
            # Adicionei a key="new_val_input"
            new_idx_val = st.number_input(
                "Valor", 
                min_value=0.0, 
                step=0.01, 
                format="%.2f", 
                label_visibility="collapsed",
                key="new_val_input"
            )
            
        with c_new3:
            if st.button("Adicionar", use_container_width=True):
                if new_idx_name:
                    try:
                        # 1. Grava no Banco
                        supabase.table("market_indices").insert({
                            "name": new_idx_name, 
                            "value": new_idx_val
                        }).execute()
                        
                        st.toast("✅ Índice criado com sucesso!", icon="✨")
                        
                        # 2. A VASSOURA: Limpa os campos antes de recarregar
                        st.session_state["new_name_input"] = ""  # Limpa texto
                        st.session_state["new_val_input"] = 0.0  # Zera número
                        
                        time.sleep(0.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Nome obrigatório")

    st.markdown("---") 

    # 2. TABELA DE EDIÇÃO
    try:
        indices = get_market_indices(supabase)
    except Exception as e:
        st.error(f"Erro ao buscar índices: {e}")
        return

    if not indices:
        st.info("Nenhum índice cadastrado.")
        return

    # === CABEÇALHO DA TABELA ===
    c_h1, c_h2, c_h3 = st.columns([3, 2, 1])
    c_h1.markdown("**Nome do Índice**")
    c_h2.markdown("**Taxa Atual (%)**")
    c_h3.markdown("**Ação**")
    
    # === LINHAS DA TABELA ===
    for idx in indices:
        c1, c2, c3 = st.columns([3, 2, 1])
        
        with c1:
            edited_name = st.text_input(
                "Nome",
                value=idx['name'],
                label_visibility="collapsed",
                key=f"name_{idx['id']}"
            )
        
        with c2:
            edited_val = st.number_input(
                "Valor",
                value=float(idx['value']),
                step=0.01,
                format="%.2f",
                label_visibility="collapsed",
                key=f"val_{idx['id']}"
            )
        
        with c3:
            if st.button("💾 Salvar", key=f"btn_{idx['id']}", use_container_width=True):
                try:
                    supabase.table("market_indices").update({
                        "name": edited_name,
                        "value": edited_val
                    }).eq("id", idx['id']).execute()
                    
                    st.toast(f"✅ {edited_name} atualizado!", icon="💾")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_admin_indices()