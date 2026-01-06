"""
Módulo de Autenticação
Gerencia login, logout e verificação de permissões de usuários via Supabase Auth.
"""
import streamlit as st
from supabase import Client


def login(supabase: Client, email: str, password: str) -> dict:
    """
    Realiza login do usuário usando Supabase Auth.
    
    Args:
        supabase: Cliente Supabase
        email: Email do usuário
        password: Senha do usuário
        
    Returns:
        dict com dados do usuário ou None se falhar
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        st.error(f"Erro no login: {str(e)}")
        return None


def logout(supabase: Client):
    """
    Realiza logout do usuário.
    
    Args:
        supabase: Cliente Supabase
    """
    try:
        supabase.auth.sign_out()
        # Limpar session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    except Exception as e:
        st.error(f"Erro no logout: {str(e)}")


def is_admin(user_data: dict) -> bool:
    """
    Verifica se o usuário tem permissões de administrador.
    
    Args:
        user_data: Dados do usuário retornados pelo login
        
    Returns:
        bool: True se for admin, False caso contrário
    """
    try:
        if not user_data or not user_data.user:
            return False
        
        user_metadata = user_data.user.user_metadata
        role = user_metadata.get('role', '')
        
        return role == 'admin'
    except:
        return False


def get_current_user(supabase: Client) -> dict:
    """
    Obtém o usuário atualmente autenticado.
    
    Args:
        supabase: Cliente Supabase
        
    Returns:
        dict com dados do usuário ou None
    """
    try:
        user = supabase.auth.get_user()
        return user
    except:
        return None


def check_authentication():
    """
    Verifica se há um usuário autenticado na sessão.
    Redireciona para login se não houver.
    
    Returns:
        bool: True se autenticado, False caso contrário
    """
    if 'user' not in st.session_state or st.session_state.user is None:
        return False
    return True


def require_admin():
    """
    Decorator/função para verificar se o usuário é admin.
    Mostra mensagem de erro se não for.
    
    Returns:
        bool: True se for admin, False caso contrário
    """
    if not check_authentication():
        st.error("❌ Você precisa estar autenticado para acessar esta página.")
        st.stop()
        return False
    
    if not st.session_state.get('is_admin', False):
        st.error("❌ Acesso negado. Esta área é restrita a administradores.")
        st.stop()
        return False
    
    return True
