import streamlit as st
import time
from utils.db import get_market_indices, update_market_index

def show_admin_indices():
    st.title("📈 Admin: Índices de Mercado")
    st.markdown("Gerencie as taxas globais usadas em todas as metodologias.")
    
    # Busca os índices atuais do banco
    try:
        indices = get_market_indices()
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return

    if not indices:
        st.warning("Nenhum índice encontrado. Rode o script SQL de configuração.")
        return

    # Estilo visual para separar os itens
    for idx in indices:
        with st.container():
            st.subheader(f"{idx['name']}")
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.markdown(f"**Valor Atual:**")
                st.markdown(f"### {float(idx['value']):.2f}%")
            
            with c2:
                # Aqui está a mágica da formatação: format="%.2f"
                # O usuário vê sempre 2 casas. Se digitar 4.6, vira 4.60 automaticamente.
                new_val = st.number_input(
                    f"Novo valor para {idx['name']}",
                    value=float(idx['value']),
                    format="%.2f", 
                    step=0.01,
                    key=f"input_{idx['id']}"
                )
                
                if st.button(f"💾 Atualizar {idx['name']}", key=f"btn_{idx['id']}"):
                    try:
                        # Envia para o banco
                        update_market_index(idx['name'], new_val)
                        st.success(f"✅ {idx['name']} atualizado para {new_val:.2f}%!")
                        time.sleep(1) # Dá um tempinho para ler a mensagem
                        st.rerun()    # Recarrega a página para mostrar o valor novo
                    except Exception as e:
                        # Agora o erro vai mostrar o DETALHE real se falhar
                        st.error(f"❌ Falha ao salvar: {e}")
            
            st.divider()

if __name__ == "__main__":
    show_admin_indices()
