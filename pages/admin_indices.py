import streamlit as st
from utils.db import get_market_indices, get_supabase_client, delete_market_index

# === CALLBACKS (Evitam erro de estado) ===

def save_new_index_callback():
    """Callback para salvar novo índice (previne erro de widget state)."""
    supabase = st.session_state['supabase']
    new_name = st.session_state.get("new_name_input", "")
    new_val = st.session_state.get("new_val_input", 0.0)
    
    if new_name:
        try:
            supabase.table("market_indices").insert({
                "name": new_name, 
                "value": new_val
            }).execute()
            
            st.toast("✅ Índice criado com sucesso!", icon="✨")
            
            # Limpa os campos DENTRO do callback (evita erro)
            st.session_state["new_name_input"] = ""
            st.session_state["new_val_input"] = 0.0
            
        except Exception as e:
            st.error(f"Erro ao criar índice: {e}")
    else:
        st.warning("Nome obrigatório")


def delete_index_callback(index_id, index_name):
    """Callback para marcar índice para confirmação de exclusão."""
    # Apenas marca para confirmação, não deleta ainda
    st.session_state['pending_delete'] = {
        'index_id': index_id,
        'index_name': index_name
    }


def confirm_delete_callback():
    """Callback que realmente executa a exclusão após confirmação."""
    supabase = st.session_state['supabase']
    pending = st.session_state.get('pending_delete')
    confirmation_text = st.session_state.get('delete_confirmation_input', '')
    
    if pending and confirmation_text == "DELETAR":
        if delete_market_index(supabase, pending['index_id']):
            st.toast(f"🗑️ Índice '{pending['index_name']}' deletado!", icon="✅")
            # Limpa o estado de confirmação
            st.session_state['pending_delete'] = None
            st.session_state['delete_confirmation_input'] = ''
        else:
            st.error("Erro ao deletar índice")
    elif confirmation_text != "DELETAR":
        st.warning("Digite exatamente 'DELETAR' para confirmar.")


def cancel_delete_callback():
    """Callback para cancelar a exclusão."""
    st.session_state['pending_delete'] = None
    st.session_state['delete_confirmation_input'] = ''


def update_index_callback(index_id, index_name):
    """Callback para atualizar índice."""
    supabase = st.session_state['supabase']
    edited_name = st.session_state.get(f"name_{index_id}")
    edited_val = st.session_state.get(f"val_{index_id}")
    
    try:
        supabase.table("market_indices").update({
            "name": edited_name,
            "value": edited_val
        }).eq("id", index_id).execute()
        
        st.toast(f"✅ {index_name} atualizado!", icon="💾")
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")


# === INTERFACE PRINCIPAL ===

def show_admin_indices():
    st.title("📈 Admin: Índices de Mercado")
    
    # 1. CONEXÃO (Salva no session_state para callbacks)
    try:
        supabase = get_supabase_client()
        st.session_state['supabase'] = supabase
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return

    # === ÁREA DE CRIAÇÃO ===
    with st.expander("➕ Adicionar Novo Índice", expanded=False):
        c_new1, c_new2, c_new3 = st.columns([3, 2, 1])
        
        with c_new1:
            st.text_input(
                "Nome", 
                placeholder="Ex: IGPM", 
                label_visibility="collapsed",
                key="new_name_input" 
            )
        
        with c_new2:
            st.number_input(
                "Valor", 
                min_value=0.0, 
                step=0.01, 
                format="%.2f", 
                label_visibility="collapsed",
                key="new_val_input"
            )
            
        with c_new3:
            st.button(
                "Adicionar", 
                use_container_width=True,
                on_click=save_new_index_callback,
                type="primary"
            )
    st.markdown("---")
    
    # === CONFIRMAÇÃO DE EXCLUSÃO (Se houver índice marcado para deletar) ===
    if st.session_state.get('pending_delete'):
        pending = st.session_state['pending_delete']
        
        st.warning(f"⚠️ **CONFIRMAR EXCLUSÃO:** Você está prestes a deletar o índice **'{pending['index_name']}'**")
        
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
 

    # === TABELA DE EDIÇÃO ===
    try:
        indices = get_market_indices(supabase)
    except Exception as e:
        st.error(f"Erro ao buscar índices: {e}")
        return

    if not indices:
        st.info("Nenhum índice cadastrado.")
        return

    # === CABEÇALHO DA TABELA ===
    c_h1, c_h2, c_h3, c_h4 = st.columns([3, 2, 1, 1])
    c_h1.markdown("**Nome do Índice**")
    c_h2.markdown("**Taxa Atual (%)**")
    c_h3.markdown("**Salvar**")
    c_h4.markdown("**Deletar**")
    
    # === LINHAS DA TABELA ===
    for idx in indices:
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        
        with c1:
            st.text_input(
                "Nome",
                value=idx['name'],
                label_visibility="collapsed",
                key=f"name_{idx['id']}"
            )
        
        with c2:
            st.number_input(
                "Valor",
                value=float(idx['value']),
                step=0.01,
                format="%.2f",
                label_visibility="collapsed",
                key=f"val_{idx['id']}"
            )
        
        with c3:
            st.button(
                "💾", 
                key=f"btn_save_{idx['id']}", 
                use_container_width=True,
                on_click=update_index_callback,
                args=(idx['id'], idx['name']),
                help="Salvar alterações"
            )
        
        with c4:
            st.button(
                "🗑️", 
                key=f"btn_del_{idx['id']}", 
                use_container_width=True,
                on_click=delete_index_callback,
                args=(idx['id'], idx['name']),
                help="Deletar índice",
                type="secondary"
            )

if __name__ == "__main__":
    show_admin_indices()