import streamlit as st
import time
from utils.db import get_market_indices, update_market_index, get_supabase_client

def show_admin_indices():
    st.title("📈 Admin: Índices de Mercado")
    st.markdown("Gerencie as taxas globais usadas em todas as metodologias.")
    
    # 1. CONEXÃO: Criar o "crachá" do Supabase
    try:
        supabase = get_supabase_client()
    except Exception as e:
        st.error(f"Erro crítico: Não foi possível iniciar conexão com banco. Detalhes: {e}")
        return

    # 2. LEITURA: Buscar os índices passando o crachá
    try:
        indices = get_market_indices(supabase) # <--- AQUI ESTAVA O ERRO, agora passamos o supabase
    except Exception as e:
        st.error(f"Erro ao buscar índices no banco: {e}")
        return

    if not indices:
        st.warning("Nenhum índice encontrado. Rode o script SQL de configuração no Supabase.")
        return

    # 3. INTERFACE: Mostrar e editar
    for idx in indices:
        with st.container():
            st.subheader(f"{idx['name']}")
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.markdown(f"**Valor Atual:**")
                st.markdown(f"### {float(idx['value']):.2f}%")
            
            with c2:
                # Input formatado com 2 casas decimais
                new_val = st.number_input(
                    f"Novo valor para {idx['name']}",
                    value=float(idx['value']),
                    format="%.2f", 
                    step=0.01,
                    key=f"input_{idx['id']}"
                )
                
                if st.button(f"💾 Atualizar {idx['name']}", key=f"btn_{idx['id']}"):
                    try:
                        # 4. GRAVAÇÃO: Passamos o supabase aqui também
                        update_market_index(supabase, idx['name'], new_val) 
                        st.success(f"✅ {idx['name']} atualizado para {new_val:.2f}%!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Falha ao salvar: {e}")
            
            st.divider()

if __name__ == "__main__":
    show_admin_indices()
