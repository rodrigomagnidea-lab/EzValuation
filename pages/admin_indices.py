"""
Página de Administração de Índices de Mercado
Permite ao Admin visualizar e editar os índices de mercado (IPCA, NTN-B, CDI, etc).
"""
import streamlit as st
from utils.auth import require_admin
from utils.db import get_supabase_client, get_market_indices, update_market_index


def main():
    """Função principal da página de índices."""
    require_admin()
    
    st.title("📈 Gerenciamento de Índices de Mercado")
    st.markdown("Configure os índices de mercado que serão utilizados nos cálculos de valuation.")
    st.markdown("---")
    
    # Inicializar cliente Supabase
    supabase = get_supabase_client()
    
    # Buscar índices atuais
    indices = get_market_indices(supabase)
    
    if not indices:
        st.info("Nenhum índice cadastrado ainda. Os índices devem ser criados via SQL.")
        st.code("""
-- Exemplo de inserção de índices:
INSERT INTO market_indices (name, value, unit, description) VALUES
('IPCA', 4.5, '%', 'Índice de Preços ao Consumidor Amplo'),
('NTN-B', 6.0, '%', 'Tesouro IPCA+ (NTN-B)'),
('CDI', 10.5, '%', 'Certificado de Depósito Interbancário'),
('SELIC', 10.75, '%', 'Taxa básica de juros');
        """, language="sql")
        return
    
    st.success(f"✅ {len(indices)} índice(s) cadastrado(s)")
    st.markdown("---")
    
    # Exibir e editar cada índice
    st.subheader("📊 Índices Disponíveis")
    
    # Organizar em colunas para melhor visualização
    cols_per_row = 2
    
    for i in range(0, len(indices), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(indices):
                index = indices[idx]
                
                with cols[j]:
                    render_index_card(supabase, index)
    
    st.markdown("---")
    
    # Histórico de atualizações
    with st.expander("📜 Histórico de Atualizações"):
        st.info("Funcionalidade de histórico será implementada em versão futura.")
        st.caption("Todas as alterações são registradas automaticamente com timestamp.")


def render_index_card(supabase, index):
    """Renderiza um card editável para um índice."""
    
    with st.container():
        # Header do card
        st.markdown(f"### {index['name']}")
        
        if index.get('description'):
            st.caption(index['description'])
        
        # Valor atual destacado
        current_value = float(index['value'])
        unit = index.get('unit', '%')
        
        st.metric(
            label="Valor Atual",
            value=f"{current_value:.2f}{unit}",
            delta=None
        )
        
        # Formulário de edição
        with st.form(key=f"form_{index['id']}"):
            st.markdown("**Atualizar Valor:**")
            
            new_value = st.number_input(
                f"Novo valor ({unit})",
                value=current_value,
                step=0.01,
                format="%.2f",
                key=f"input_{index['id']}"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                submit = st.form_submit_button(
                    "💾 Atualizar",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                info = st.form_submit_button(
                    "ℹ️ Info",
                    use_container_width=True
                )
            
            if submit:
                if new_value != current_value:
                    result = update_market_index(supabase, index['id'], new_value)
                    if result:
                        st.success(f"✅ {index['name']} atualizado para {new_value:.2f}{unit}")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao atualizar índice.")
                else:
                    st.info("⚠️ Valor não foi alterado.")
            
            if info:
                st.info(f"""
**Informações do Índice:**
- **ID**: {index['id']}
- **Nome**: {index['name']}
- **Unidade**: {unit}
- **Última atualização**: {index.get('updated_at', 'N/A')}
                """)
        
        st.markdown("---")


if __name__ == "__main__":
    main()
