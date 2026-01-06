"""
Módulo de Sidebar Centralizada
Gerencia a exibição do menu lateral em todas as páginas da aplicação.
"""
import streamlit as st
from utils.auth import logout
from utils.db import get_supabase_client


def show_sidebar():
    """
    Renderiza a sidebar com navegação, informações do usuário e logout.
    Deve ser chamada no início de cada página para manter consistência.
    
    Returns:
        str: A página selecionada pelo usuário
    """
    with st.sidebar:
        # Logo e título
        st.markdown("### 📊 EzValuation")
        st.markdown("---")
        
        # Informações do usuário
        if st.session_state.get('user') and hasattr(st.session_state.user, 'user'):
            user_email = st.session_state.user.user.email
            st.markdown(f"👤 **{user_email}**")
        
        # Badge de administrador
        if st.session_state.get('is_admin', False):
            st.success("🔧 Administrador")
        else:
            st.info("👤 Usuário")
        
        st.markdown("---")
        
        # Menu de navegação
        st.subheader("🧭 Navegação")
        
        # Navegação baseada em role
        if st.session_state.get('is_admin', False):
            page = st.radio(
                "Selecione a página:",
                options=[
                    "📊 Nova Análise",
                    "📂 Minhas Análises",
                    "💰 Valuation",
                    "🔧 Admin: Metodologias",
                    "📈 Admin: Índices"
                ],
                label_visibility="collapsed"
            )
        else:
            page = st.radio(
                "Selecione a página:",
                options=[
                    "📊 Nova Análise",
                    "📂 Minhas Análises",
                    "💰 Valuation"
                ],
                label_visibility="collapsed"
            )
        
        st.markdown("---")
        
        # Botão de logout
        if st.button("🚪 Sair", use_container_width=True):
            try:
                supabase = get_supabase_client()
                logout(supabase)
            except:
                pass
            st.session_state.clear()
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.caption("EzValuation v1.0")
        st.caption("© 2026")
    
    return page
