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

    # === ÁREA DE CRIAÇÃO (Compacta) ===
    with st.expander("➕ Novo Índice", expanded=False):
        c_new1, c_new2, c_new3 = st.columns([3, 2, 1])
        with c_new1:
            new_idx_name = st.text_input("Nome", placeholder="Ex: IGPM")
        with c_new2:
            new_idx_val = st.number_input("Valor (%)", min_value=0.0, step=0.01, format="%.2f")
        with c_new3:
            st.write("") # Espaçamento para alinhar botão
            st.write("") 
            if st.button("Criar"):
                if new_idx_name:
                    try:
                        supabase.table("market_indices").insert({
                            "name": new_idx_name, 
                            "value": new_idx_val
                        }).execute()
                        st.success("Criado!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.divider()

    # 2. TABELA DE EDIÇÃO
    try:
        indices = get_market_indices(supabase)
    except Exception as e:
        st.error(f"Erro ao buscar índices: {e}")
        return

    if not indices:
        st.info("Nenhum índice cadastrado.")
        return

    # --- CABEÇALHO DA TABELA ---
    # Cria uma linha visual de títulos
    c_head1, c_head2, c_head3 = st.columns([3, 2, 1])
    c_head1.markdown("**Nome do Índice**")
    c_head2.markdown("**Valor (%)**")
    c_head3.markdown("**Ação**")
    
    st.markdown("---") # Linha fina separadora

    # --- LINHAS DA TABELA ---
    for idx in indices:
        # Layout de Grid: 3 Colunas alinhadas
        c1, c2, c3 = st.columns([3, 2, 1])
        
        with c1:
            # Input de Nome (sem label visível para parecer tabela)
            edited_name = st.text_input(
                "Nome",
                value=idx['name'],
                label_visibility="collapsed",
                key=f"name_{idx['id']}"
            )
        
        with c2:
            # Input de Valor
            edited_val = st.number_input(
                "Valor",
                value=float(idx['value']),
                step=0.01,
                format="%.2f",
                label_visibility="collapsed",
                key=f"val_{idx['id']}"
            )
        
        with c3:
            # Botão Salvar Discreto
            # O use_container_width faz o botão preencher a coluna, ficando alinhado
            if st.button("💾 Salvar", key=f"btn_{idx['id']}", use_container_width=True):
                try:
                    supabase.table("market_indices").update({
                        "name": edited_name,
                        "value": edited_val
                    }).eq("id", idx['id']).execute()
                    
                    st.toast(f"✅ {edited_name} salvo!", icon="💾")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.toast(f"❌ Erro: {e}")

        # Pequeno divisor entre linhas (opcional, pode remover se quiser mais compacto ainda)
        # st.divider() 

if __name__ == "__main__":
    show_admin_indices()
