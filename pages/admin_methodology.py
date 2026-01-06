"""
Página de Administração de Metodologias
Permite ao Admin criar e gerenciar metodologias, pilares, critérios e faixas de avaliação.
"""
import streamlit as st
from utils.auth import require_admin
from utils.db import (
    get_supabase_client,
    get_all_methodologies,
    create_methodology,
    set_active_methodology,
    get_pillars_by_methodology,
    create_pillar,
    update_pillar,
    delete_pillar,
    get_criteria_by_pillar,
    create_criterion,
    update_criterion,
    delete_criterion,
    get_ranges_by_criterion,
    create_range,
    delete_range,
    get_full_methodology_tree
)


def main():
    """Função principal da página de administração."""
    require_admin()
    
    st.title("🔧 Painel Administrativo - Metodologias")
    st.markdown("---")
    
    # Inicializar cliente Supabase
    supabase = get_supabase_client()
    
    # Tabs principais
    tab1, tab2 = st.tabs(["📋 Gerenciar Metodologias", "👁️ Visualizar Estrutura"])
    
    with tab1:
        manage_methodologies_tab(supabase)
    
    with tab2:
        preview_methodology_tab(supabase)


def manage_methodologies_tab(supabase):
    """Tab para criar e editar metodologias."""
    
    st.subheader("Gerenciar Metodologias")
    
    # Criar nova metodologia
    with st.expander("➕ Criar Nova Metodologia", expanded=False):
        new_version = st.text_input(
            "Versão da Metodologia",
            placeholder="Ex: FII Tijolo v1.3",
            key="new_version",
            help="Escolha um nome descritivo para a versão da metodologia"
        )
        
        st.caption("💡 Os índices de mercado (IPCA, NTN-B, CDI, etc) são configurados globalmente na página 'Admin: Índices'.")
        
        if st.button("Criar Metodologia", type="primary"):
            if new_version:
                result = create_methodology(supabase, new_version)
                if result:
                    st.success(f"✅ Metodologia '{new_version}' criada com sucesso!")
                    st.rerun()
            else:
                st.error("Por favor, informe a versão da metodologia.")

    
    st.markdown("---")
    
    # Listar metodologias existentes
    methodologies = get_all_methodologies(supabase)
    
    if not methodologies:
        st.info("Nenhuma metodologia cadastrada ainda.")
        return
    
    # Seletor de metodologia
    st.subheader("Editar Metodologia Existente")
    
    methodology_options = {m['version']: m for m in methodologies}
    selected_version = st.selectbox(
        "Selecione uma metodologia",
        options=list(methodology_options.keys()),
        format_func=lambda x: f"{'🟢 ATIVA' if methodology_options[x]['is_active'] else '⚪'} {x}"
    )
    
    if selected_version:
        selected_methodology = methodology_options[selected_version]
        
        # Ativar/indicar metodologia ativa
        if not selected_methodology['is_active']:
            if st.button("✅ Ativar esta Metodologia", type="primary"):
                if set_active_methodology(supabase, selected_methodology['id']):
                    st.success("Metodologia ativada!")
                    st.rerun()
        else:
            st.success("✅ Esta é a metodologia ativa")
        
        st.markdown("---")
        
        # Gerenciar Pilares desta metodologia
        manage_pillars(supabase, selected_methodology['id'])



def manage_pillars(supabase, methodology_id):
    """Gerencia pilares de uma metodologia."""
    
    st.subheader("🏛️ Pilares da Metodologia")
    
    # Adicionar novo pilar
    with st.expander("➕ Adicionar Pilar", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pillar_name = st.text_input("Nome do Pilar", placeholder="Ex: Gestão e Governança", key="new_pillar_name")
        with col2:
            pillar_weight = st.number_input("Peso", value=1.0, min_value=0.1, step=0.1, key="new_pillar_weight")
        
        pillar_desc = st.text_area("Descrição", placeholder="Descrição do pilar...", key="new_pillar_desc")
        
        if st.button("Adicionar Pilar", key="add_pillar_btn"):
            if pillar_name:
                result = create_pillar(supabase, methodology_id, pillar_name, pillar_weight, pillar_desc)
                if result:
                    st.success(f"✅ Pilar '{pillar_name}' adicionado!")
                    st.rerun()
            else:
                st.error("Por favor, informe o nome do pilar.")
    
    # Listar pilares existentes
    pillars = get_pillars_by_methodology(supabase, methodology_id)
    
    if not pillars:
        st.info("Nenhum pilar cadastrado ainda.")
        return
    
    # Exibir cada pilar
    for idx, pillar in enumerate(pillars):
        with st.expander(f"🏛️ {pillar['name']} (Peso: {pillar['weight']})", expanded=False):
            
            # Editar pilar
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                edit_name = st.text_input(
                    "Nome",
                    value=pillar['name'],
                    key=f"edit_pillar_name_{pillar['id']}"
                )
            with col2:
                edit_weight = st.number_input(
                    "Peso",
                    value=float(pillar['weight']),
                    min_value=0.1,
                    step=0.1,
                    key=f"edit_pillar_weight_{pillar['id']}"
                )
            with col3:
                if st.button("💾 Salvar", key=f"save_pillar_{pillar['id']}"):
                    edit_desc = st.session_state.get(f"edit_pillar_desc_{pillar['id']}", pillar.get('description', ''))
                    update_pillar(supabase, pillar['id'], edit_name, edit_weight, edit_desc)
                    st.success("Pilar atualizado!")
                    st.rerun()
            
            edit_desc = st.text_area(
                "Descrição",
                value=pillar.get('description', ''),
                key=f"edit_pillar_desc_{pillar['id']}"
            )
            
            # Deletar pilar
            if st.button(f"🗑️ Deletar Pilar '{pillar['name']}'", key=f"del_pillar_{pillar['id']}", type="secondary"):
                delete_pillar(supabase, pillar['id'])
                st.success("Pilar deletado!")
                st.rerun()
            
            st.markdown("---")
            
            # Gerenciar critérios deste pilar
            manage_criteria(supabase, pillar['id'], pillar['name'])


def manage_criteria(supabase, pillar_id, pillar_name):
    """Gerencia critérios de um pilar."""
    
    st.markdown(f"#### 📊 Critérios do Pilar: {pillar_name}")
    
    # Adicionar novo critério
    with st.expander("➕ Adicionar Critério", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            criterion_name = st.text_input(
                "Nome do Critério",
                placeholder="Ex: Histórico da Gestora",
                key=f"new_criterion_name_{pillar_id}"
            )
        with col2:
            criterion_type = st.selectbox(
                "Tipo",
                options=['numeric', 'percent', 'boolean', 'categorical'],
                key=f"new_criterion_type_{pillar_id}"
            )
        
        col3, col4 = st.columns([1, 3])
        
        with col3:
            criterion_unit = st.text_input(
                "Unidade",
                placeholder="Ex: anos, %, R$",
                key=f"new_criterion_unit_{pillar_id}"
            )
        with col4:
            criterion_rule = st.text_input(
                "Regra de Avaliação",
                placeholder="Ex: Ideal > 10 anos de histórico",
                key=f"new_criterion_rule_{pillar_id}"
            )
        
        if st.button("Adicionar Critério", key=f"add_criterion_btn_{pillar_id}"):
            if criterion_name:
                result = create_criterion(
                    supabase, pillar_id, criterion_name,
                    criterion_type, criterion_unit, criterion_rule
                )
                if result:
                    st.success(f"✅ Critério '{criterion_name}' adicionado!")
                    st.rerun()
            else:
                st.error("Por favor, informe o nome do critério.")
    
    # Listar critérios existentes
    criteria = get_criteria_by_pillar(supabase, pillar_id)
    
    if not criteria:
        st.info(f"Nenhum critério cadastrado para o pilar '{pillar_name}'.")
        return
    
    # Exibir cada critério
    for criterion in criteria:
        with st.container():
            st.markdown(f"##### 📊 {criterion['name']}")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.text(f"Tipo: {criterion['type']} | Unidade: {criterion.get('unit', 'N/A')}")
            with col2:
                if st.button("✏️ Editar", key=f"edit_criterion_{criterion['id']}", type="secondary"):
                    st.info("Use os campos abaixo para editar")
            with col3:
                if st.button("🗑️ Deletar", key=f"del_criterion_{criterion['id']}", type="secondary"):
                    delete_criterion(supabase, criterion['id'])
                    st.success("Critério deletado!")
                    st.rerun()
            
            if criterion.get('rule_description'):
                st.caption(f"📏 Regra: {criterion['rule_description']}")
            
            # Gerenciar faixas (ranges) deste critério
            manage_ranges(supabase, criterion['id'], criterion['name'], criterion['type'])
            
            st.markdown("---")


def manage_ranges(supabase, criterion_id, criterion_name, criterion_type):
    """Gerencia faixas (ranges) de um critério."""
    
    st.markdown(f"**Faixas de Pontuação**")
    
    # Adicionar nova faixa
    with st.expander("➕ Adicionar Faixa", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            range_min = st.text_input("Mínimo", placeholder="0 ou 'Não'", key=f"new_range_min_{criterion_id}")
        with col2:
            range_max = st.text_input("Máximo", placeholder="10 ou 'Sim'", key=f"new_range_max_{criterion_id}")
        with col3:
            range_points = st.number_input("Pontos", value=0.0, step=0.5, key=f"new_range_points_{criterion_id}")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            range_label = st.text_input("Label", placeholder="Ex: Excelente", key=f"new_range_label_{criterion_id}")
        with col5:
            range_color = st.selectbox(
                "Cor",
                options=['green', 'yellow', 'red'],
                key=f"new_range_color_{criterion_id}"
            )
        with col6:
            range_impact = st.selectbox(
                "Impacto",
                options=['neutral', 'penalty_light', 'penalty_structural'],
                key=f"new_range_impact_{criterion_id}"
            )
        
        if st.button("Adicionar Faixa", key=f"add_range_btn_{criterion_id}"):
            if range_label:
                result = create_range(
                    supabase, criterion_id,
                    range_min if range_min else None,
                    range_max if range_max else None,
                    range_label, range_points, range_color, range_impact
                )
                if result:
                    st.success(f"✅ Faixa '{range_label}' adicionada!")
                    st.rerun()
            else:
                st.error("Por favor, informe o label da faixa.")
    
    # Listar faixas existentes
    ranges = get_ranges_by_criterion(supabase, criterion_id)
    
    if not ranges:
        st.warning(f"⚠️ Nenhuma faixa cadastrada para '{criterion_name}'.")
        return
    
    # Exibir faixas como tabela
    for r in ranges:
        color_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(r['color'], "⚪")
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.text(f"{color_emoji} {r['label']}")
        with col2:
            min_display = r['min'] if r['min'] else '-∞'
            max_display = r['max'] if r['max'] else '+∞'
            st.caption(f"[{min_display}, {max_display}]")
        with col3:
            st.caption(f"Pts: {r['points']}")
        with col4:
            st.caption(f"{r['impact']}")
        with col5:
            if st.button("🗑️", key=f"del_range_{r['id']}", help="Deletar faixa"):
                delete_range(supabase, r['id'])
                st.success("Faixa deletada!")
                st.rerun()


def preview_methodology_tab(supabase):
    """Tab para visualizar a estrutura completa da metodologia."""
    
    st.subheader("👁️ Visualização Completa da Metodologia")
    
    methodologies = get_all_methodologies(supabase)
    
    if not methodologies:
        st.info("Nenhuma metodologia cadastrada.")
        return
    
    methodology_options = {m['version']: m for m in methodologies}
    selected_version = st.selectbox(
        "Selecione uma metodologia para visualizar",
        options=list(methodology_options.keys()),
        key="preview_selector"
    )
    
    if selected_version:
        selected_methodology = methodology_options[selected_version]
        
        # Buscar árvore completa
        tree = get_full_methodology_tree(supabase, selected_methodology['id'])
        
        if not tree:
            st.error("Erro ao carregar metodologia.")
            return
        
        # Exibir header
        st.markdown(f"### {tree['version']}")
        
        status = "🟢 ATIVA" if tree['is_active'] else "⚪ Inativa"
        st.markdown(f"**Status:** {status}")
        
        st.caption("💡 Os índices de mercado (IPCA, NTN-B, etc) são gerenciados globalmente na página 'Admin: Índices'.")
        
        st.markdown("---")

        
        # Exibir pilares
        if 'pillars' not in tree or not tree['pillars']:
            st.info("Esta metodologia ainda não possui pilares.")
            return
        
        for pillar in tree['pillars']:
            with st.expander(f"🏛️ {pillar['name']} (Peso: {pillar['weight']})", expanded=True):
                if pillar.get('description'):
                    st.caption(pillar['description'])
                
                if 'criteria' not in pillar or not pillar['criteria']:
                    st.info("Nenhum critério cadastrado neste pilar.")
                    continue
                
                for criterion in pillar['criteria']:
                    st.markdown(f"**📊 {criterion['name']}**")
                    st.caption(f"Tipo: {criterion['type']} | Unidade: {criterion.get('unit', 'N/A')}")
                    
                    if criterion.get('rule_description'):
                        st.info(f"📏 {criterion['rule_description']}")
                    
                    # Exibir ranges
                    if 'ranges' in criterion and criterion['ranges']:
                        for r in criterion['ranges']:
                            color_map = {
                                'green': '#28a745',
                                'yellow': '#ffc107',
                                'red': '#dc3545'
                            }
                            bg_color = color_map.get(r['color'], '#cccccc')
                            
                            min_display = r['min'] if r['min'] else '-∞'
                            max_display = r['max'] if r['max'] else '+∞'
                            
                            st.markdown(
                                f"""
                                <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                                    <strong>{r['label']}</strong>: [{min_display}, {max_display}] = {r['points']} pts
                                    <br><em>{r['impact']}</em>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        st.warning("⚠️ Sem faixas definidas")
                    
                    st.markdown("---")


if __name__ == "__main__":
    main()
