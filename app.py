"""
EzValuation - Investment Thesis Generator
Aplicação principal com controle de acesso e navegação.
"""
import streamlit as st
from utils.auth import login, logout, is_admin, check_authentication
from utils.db import get_supabase_client


def main():
    """Função principal da aplicação."""
    
    # Configuração da página
    st.set_page_config(
        page_title="EzValuation",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicializar session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    
    # Verificar autenticação
    if st.session_state.user is None:
        show_login_page()
    else:
        show_main_app()


def show_login_page():
    """Exibe a página de login."""
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 50px 0 30px 0;">
                <h1 style="font-size: 48px; margin-bottom: 10px;">📊 EzValuation</h1>
                <p style="font-size: 20px; color: #666;">Investment Thesis Generator</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Formulário de login
        with st.form("login_form"):
            st.subheader("🔐 Login")
            
            email = st.text_input("Email", placeholder="seu@email.com")
            password = st.text_input("Senha", type="password", placeholder="••••••••")
            
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submit:
                if email and password:
                    with st.spinner("Autenticando..."):
                        supabase = get_supabase_client()
                        user_data = login(supabase, email, password)
                        
                        if user_data:
                            st.session_state.user = user_data
                            st.session_state.is_admin = is_admin(user_data)
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Email ou senha inválidos.")
                else:
                    st.error("⚠️ Por favor, preencha todos os campos.")
        
        # Informações adicionais
        with st.expander("ℹ️ Sobre o EzValuation"):
            st.markdown(
                """
                O **EzValuation** é uma plataforma completa para análise de investimentos em 
                Fundos Imobiliários (FIIs).
                
                **Recursos:**
                - 📊 Análise estruturada baseada em metodologias personalizáveis
                - 💰 Calculadoras de valuation (Gordon, IPCA+, FCFE)
                - 📄 Geração de relatórios em PDF
                - 🔧 Painel administrativo para gestão de metodologias
                
                **Como usar:**
                1. Faça login com suas credenciais
                2. Escolha um FII para analisar
                3. Preencha o checklist de avaliação
                4. Visualize o score e exporte o relatório
                
                ---
                
                *Para acesso administrativo, seu usuário deve ter a role 'admin' configurada.*
                """
            )


def show_main_app():
    """Exibe a aplicação principal após autenticação."""
    
    # Sidebar com navegação
    with st.sidebar:
        st.markdown("### 📊 EzValuation")
        st.markdown("---")
        
        # Informações do usuário
        user_email = st.session_state.user.user.email
        st.markdown(f"👤 **{user_email}**")
        
        if st.session_state.is_admin:
            st.success("🔧 Administrador")
        else:
            st.info("👤 Usuário")
        
        st.markdown("---")
        
        # Menu de navegação
        st.subheader("🧭 Navegação")
        
        # Navegação baseada em role
        if st.session_state.is_admin:
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
            supabase = get_supabase_client()
            logout(supabase)
            st.success("Logout realizado com sucesso!")
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.caption("EzValuation v1.0")
        st.caption("© 2026")
    
    # Conteúdo principal baseado na página selecionada
    if page == "🔧 Admin: Metodologias":
        from pages import admin_methodology
        admin_methodology.main()
    
    elif page == "📈 Admin: Índices":
        from pages.admin_indices import show_admin_indices
        show_admin_indices()
    
    elif page in ["📊 Nova Análise", "📂 Minhas Análises", "💰 Valuation"]:
        from pages import analysis_wizard
        analysis_wizard.main()
    
    else:
        st.info("Página em desenvolvimento.")


if __name__ == "__main__":
    main()
