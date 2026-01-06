"""
Página Admin: Gerenciar Metodologias
Sistema simplificado com callbacks e confirmação de exclusão.
"""
import streamlit as st
from utils.db import (
    get_supabase_client,
    get_methodologies,
    create_methodology,
    set_active_methodology,
    delete_methodology
)

# === CALLBACKS (Evitam erro de estado) ===

def save_new_methodology_callback():
    """Callback para salvar nova metodologia (previne erro de widget state)."""
    supabase = st.session_state['supabase']
    new_version = st.session_state.get("new_version_input", "")
    
    if new_version:
        try:
            create_methodology(supabase, new_version)
            st.toast("✅ Metodologia criada com sucesso!", icon="✨")
            
            # Limpa o campo DENTRO do callback (evita erro)
            st.session_state["new_version_input"] = ""
            
        except Exception as e:
            st.error(f"Erro ao criar metodologia: {e}")
    else:
        st.warning("Nome/versão obrigatório")


def activate_methodology_callback(methodology_id, version):
    """Callback para ativar metodologia."""
    supabase = st.session_state['supabase']
    
    if set_active_methodology(supabase, methodology_id):
        st.toast(f"✅ Metodologia '{version}' ativada!", icon="🎯")
    else:
        st.error("Erro ao ativar metodologia")


def delete_methodology_callback(methodology_id, version):
    """Callback para marcar metodologia para confirmação de exclusão."""
    # Apenas marca para confirmação, não deleta ainda
    st.session_state['pending_delete'] = {
        'methodology_id': methodology_id,
        'version': version
    }


def confirm_delete_callback():
    """Callback que realmente executa a exclusão após confirmação."""
    supabase = st.session_state['supabase']
    pending = st.session_state.get('pending_delete')
    confirmation_text = st.session_state.get('delete_confirmation_input', '')
    
    if pending and confirmation_text == "DELETAR":
        if delete_methodology(supabase, pending['methodology_id']):
            st.toast(f"🗑️ Metodologia '{pending['version']}' deletada!", icon="✅")
            # Limpa o estado de confirmação
            st.session_state['pending_delete'] = None
            st.session_state['delete_confirmation_input'] = ''
        else:
            st.error("Erro ao deletar metodologia")
    elif confirmation_text != "DELETAR":
        st.warning("Digite exatamente 'DELETAR' para confirmar.")


def cancel_delete_callback():
    """Callback para cancelar a exclusão."""
    st.session_state['pending_delete'] = None
    st.session_state['delete_confirmation_input'] = ''


# === INTERFACE PRINCIPAL ===

def show_admin_methodology():
    # Sidebar é gerenciada pelo app.py - não duplicar aqui!
    
    st.title("🛠️ Gerenciar Metodologias")
    
    # 1. CONEXÃO (Salva no session_state para callbacks)
    try:
        supabase = get_supabase_client()
        st.session_state['supabase'] = supabase
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return

    # === ÁREA DE CRIAÇÃO ===
    with st.expander("➕ Adicionar Nova Metodologia", expanded=False):
        c_new1, c_new2 = st.columns([3, 1])
        
        with c_new1:
            st.text_input(
                "Nome/Versão da Metodologia", 
                placeholder="Ex: Metodologia v2.0", 
                label_visibility="collapsed",
                key="new_version_input" 
            )
        
        with c_new2:
            st.button(
                "Criar", 
                use_container_width=True,
                on_click=save_new_methodology_callback,
                type="primary"
            )

    st.markdown("---")
    
    # === CONFIRMAÇÃO DE EXCLUSÃO (Se houver metodologia marcada para deletar) ===
    if st.session_state.get('pending_delete'):
        pending = st.session_state['pending_delete']
        
        st.warning(f"⚠️ **CONFIRMAR EXCLUSÃO:** Você está prestes a deletar a metodologia **'{pending['version']}'**")
        
        c_conf1, c_conf2, c_conf3 = st.columns([2, 1, 1])
        
        with c_conf1:
            st.text_input(
                "Digite DELETAR para confirmar:",
                key="delete_confirmation_input",
                placeholder="DELETAR",
                label_visibility="collapsed"
            )
        
        with c_conf2:
            st.button(
                "✅ Confirmar",
                key="btn_confirm_delete",
                on_click=confirm_delete_callback,
                type="primary",
                use_container_width=True
            )
        
        with c_conf3:
            st.button(
                "❌ Cancelar",
                key="btn_cancel_delete",
                on_click=cancel_delete_callback,
                use_container_width=True
            )
        
        st.markdown("---")

    # === TABELA DE METODOLOGIAS ===
    try:
        methodologies = get_methodologies(supabase)
    except Exception as e:
        st.error(f"Erro ao buscar metodologias: {e}")
        return

    if not methodologies:
        st.info("Nenhuma metodologia cadastrada.")
        return

    # === CABEÇALHO DA TABELA ===
    c_h1, c_h2, c_h3, c_h4 = st.columns([3, 1, 1, 1])
    c_h1.markdown("**Nome/Versão**")
    c_h2.markdown("**Status**")
    c_h3.markdown("**Ativar**")
    c_h4.markdown("**Deletar**")
    
    # === LINHAS DA TABELA ===
    for method in methodologies:
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        
        with c1:
            # Usa version ou name como fallback
            display_name = method.get('version') or method.get('name') or f"ID: {method['id'][:8]}"
            st.markdown(f"**{display_name}**")
        
        with c2:
            if method.get('is_active'):
                st.success("✅ Ativa")
            else:
                st.info("⚪ Inativa")
        
        with c3:
            if not method.get('is_active'):
                st.button(
                    "🎯 Ativar",
                    key=f"btn_activate_{method['id']}",
                    use_container_width=True,
                    on_click=activate_methodology_callback,
                    args=(method['id'], display_name),
                    type="primary"
                )
            else:
                st.caption("(atual)")
        
        with c4:
            st.button(
                "🗑️",
                key=f"btn_del_{method['id']}",
                use_container_width=True,
                on_click=delete_methodology_callback,
                args=(method['id'], display_name),
                help="Deletar metodologia",
                type="secondary"
            )


if __name__ == "__main__":
    show_admin_methodology()
