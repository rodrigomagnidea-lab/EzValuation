import streamlit as st
import time
from utils.db import (
    get_supabase_client, 
    get_methodologies, 
    get_pillars_by_methodology,
    get_criteria_by_pillar,
    get_thresholds_by_criterion
)

def show_admin_methodology():
    # Sidebar é gerenciada pelo app.py - não duplicar aqui!
    
    # === HEADER ===
    st.title("🛠️ Gerenciar Metodologias")

    # Conexão
    try:
        supabase = get_supabase_client()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return

    # Abas para separar Criação de Visualização
    tab_mng, tab_view = st.tabs(["📝 Gerenciar Estrutura", "👀 Visualizar Relatório"])

    # ==============================================================================
    # ABA 1: GERENCIAR (Criação e Edição)
    # ==============================================================================
    with tab_mng:
        
        # --- 1. SEÇÃO DE METODOLOGIAS ---
        st.subheader("1. Metodologia")
        
        # Container de Criação (Expansível para não poluir)
        with st.expander("➕ Criar Nova Metodologia", expanded=False):
            c_new_met, c_btn_met = st.columns([4, 1])
            new_met_name = c_new_met.text_input("Nome da Nova Metodologia", key="new_met_name", label_visibility="collapsed", placeholder="Ex: FII Tijolo - Logístico")
            
            if c_btn_met.button("Criar", key="btn_create_met", use_container_width=True):
                if new_met_name:
                    try:
                        supabase.table("methodology_config").insert({"name": new_met_name}).execute()
                        st.toast(f"✅ Metodologia '{new_met_name}' criada!")
                        # Limpa o campo
                        st.session_state["new_met_name"] = ""
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        # Seleção e Edição da Metodologia Atual
        methodologies = get_methodologies(supabase)
        if not methodologies:
            st.info("Nenhuma metodologia criada ainda.")
            return

        met_options = {m['name']: m['id'] for m in methodologies}
        selected_met_name = st.selectbox("Selecione a Metodologia para Editar:", list(met_options.keys()))
        selected_met_id = met_options[selected_met_name]

        # Área de Renomear/Ativar
        with st.container(border=True):
            c_edit1, c_edit2, c_edit3 = st.columns([3, 1, 1])
            
            # Renomear
            new_name_edit = c_edit1.text_input("Editar Nome", value=selected_met_name, label_visibility="collapsed")
            if c_edit2.button("💾 Renomear", use_container_width=True):
                if new_name_edit != selected_met_name:
                    supabase.table("methodology_config").update({"name": new_name_edit}).eq("id", selected_met_id).execute()
                    st.toast("Nome atualizado!")
                    time.sleep(1)
                    st.rerun()

            # Botão de Status (Ativo/Inativo - Visual)
            c_edit3.button("✅ Ativa", disabled=True, use_container_width=True) # Placeholder visual por enquanto

        st.markdown("---")

        # --- 2. SEÇÃO DE PILARES ---
        st.subheader(f"2. Pilares de: {selected_met_name}")

        # Criação de Pilar
        with st.expander("➕ Adicionar Novo Pilar", expanded=False):
            c_pil1, c_pil2, c_pil3 = st.columns([3, 1, 1])
            new_pil_name = c_pil1.text_input("Nome do Pilar", key="new_pil_name", placeholder="Ex: Qualidade do Imóvel")
            new_pil_weight = c_pil2.number_input("Peso", min_value=0.1, value=1.0, step=0.1, key="new_pil_weight")
            
            if c_pil3.button("Adicionar Pilar", use_container_width=True):
                if new_pil_name:
                    try:
                        supabase.table("pillar_config").insert({
                            "methodology_id": selected_met_id,
                            "name": new_pil_name,
                            "weight": new_pil_weight
                        }).execute()
                        st.toast("Pilar adicionado!")
                        # Limpeza
                        st.session_state["new_pil_name"] = ""
                        st.session_state["new_pil_weight"] = 1.0
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        # Listagem de Pilares
        pillars = get_pillars_by_methodology(supabase, selected_met_id)
        
        if not pillars:
            st.info("Nenhum pilar cadastrado nesta metodologia.")
        else:
            for pillar in pillars:
                with st.container(border=True):
                    # Cabeçalho do Pilar (Nome e Peso)
                    c_p1, c_p2, c_p3 = st.columns([4, 1, 1])
                    c_p1.markdown(f"**🏛️ {pillar['name']}**")
                    c_p2.markdown(f"Peso: `{pillar['weight']}`")
                    if c_p3.button("🗑️", key=f"del_pil_{pillar['id']}"):
                        supabase.table("pillar_config").delete().eq("id", pillar['id']).execute()
                        st.rerun()

                    # --- 3. CRITÉRIOS (Dentro do Pilar) ---
                    st.markdown("#### ↳ Critérios")
                    
                    # Criação de Critério
                    with st.expander(f"➕ Novo Critério em '{pillar['name']}'"):
                        c_crit1, c_crit2 = st.columns([3, 1])
                        c_crit3, c_crit4 = st.columns([2, 2])
                        
                        crit_name = c_crit1.text_input("Nome", key=f"cn_{pillar['id']}")
                        crit_weight = c_crit2.number_input("Peso", value=1.0, key=f"cw_{pillar['id']}")
                        crit_type = c_crit3.selectbox("Tipo", ["numeric", "boolean", "options"], key=f"ct_{pillar['id']}")
                        crit_better = c_crit4.selectbox("Melhor se...", ["Quanto Maior Melhor", "Quanto Menor Melhor"], key=f"cb_{pillar['id']}")
                        
                        if st.button("Salvar Critério", key=f"btn_save_crit_{pillar['id']}"):
                            if crit_name:
                                try:
                                    # Mapear selection para DB
                                    db_better = "higher" if crit_better == "Quanto Maior Melhor" else "lower"
                                    
                                    # Cria critério e pega ID
                                    res = supabase.table("criterion_config").insert({
                                        "pillar_id": pillar['id'],
                                        "name": crit_name,
                                        "weight": crit_weight,
                                        "criterion_type": crit_type,
                                        "better_direction": db_better
                                    }).execute()
                                    
                                    # Tenta criar faixas automáticas padrão (Opcional, mas ajuda)
                                    new_crit_id = res.data[0]['id']
                                    
                                    st.toast("Critério salvo!")
                                    # Limpeza manual
                                    st.session_state[f"cn_{pillar['id']}"] = ""
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {e}")

                    # Listar Critérios Existentes
                    criteria = get_criteria_by_pillar(supabase, pillar['id'])
                    for crit in criteria:
                        with st.status(f"📊 {crit['name']} (Peso: {crit['weight']})", expanded=False):
                            c_del_crit, _ = st.columns([1, 4])
                            if c_del_crit.button("Deletar Critério", key=f"del_crit_{crit['id']}"):
                                supabase.table("criterion_config").delete().eq("id", crit['id']).execute()
                                st.rerun()

                            # --- 4. FAIXAS (THRESHOLDS) ---
                            st.divider()
                            st.caption("Faixas de Pontuação (Thresholds)")
                            
                            # Form de Nova Faixa
                            c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns([2, 2, 2, 2, 1])
                            l_label = c_f1.text_input("Label", placeholder="Ex: Bom", key=f"l_{crit['id']}")
                            l_min = c_f2.text_input("Min", placeholder="-inf", key=f"min_{crit['id']}")
                            l_max = c_f3.text_input("Max", placeholder="0.5", key=f"max_{crit['id']}")
                            l_pt = c_f4.number_input("Pts", value=10.0, key=f"pt_{crit['id']}")
                            
                            if c_f5.button("➕", key=f"add_th_{crit['id']}"):
                                try:
                                    final_min = float(l_min) if l_min and l_min != "-inf" else -999999
                                    final_max = float(l_max) if l_max and l_max != "inf" else 999999
                                    
                                    supabase.table("threshold_range").insert({
                                        "criterion_id": crit['id'],
                                        "label": l_label,
                                        "min_value": final_min,
                                        "max_value": final_max,
                                        "score": l_pt,
                                        "color": "green" if l_pt >= 7 else "yellow" if l_pt >= 5 else "red"
                                    }).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erro nos números")

                            # Listar Faixas
                            thresholds = get_thresholds_by_criterion(supabase, crit['id'])
                            if thresholds:
                                # Tabela simples de faixas
                                for th in thresholds:
                                    cols = st.columns([2, 2, 2, 1])
                                    cols[0].write(f"🏷️ {th['label']}")
                                    cols[1].write(f"📏 {th['min_value']} a {th['max_value']}")
                                    cols[2].write(f"⭐ {th['score']}")
                                    if cols[3].button("🗑️", key=f"del_th_{th['id']}"):
                                        supabase.table("threshold_range").delete().eq("id", th['id']).execute()
                                        st.rerun()


    # ==============================================================================
    # ABA 2: VISUALIZAR (Layout Limpo)
    # ==============================================================================
    with tab_view:
        if not methodologies:
            st.warning("Crie uma metodologia primeiro.")
            return
            
        st.markdown(f"## 📑 Relatório Estrutural: {selected_met_name}")
        st.markdown("---")

        pillars = get_pillars_by_methodology(supabase, selected_met_id)
        
        for pillar in pillars:
            st.markdown(f"### 🏛️ {pillar['name']} <span style='font-size:0.7em; color:gray'>(Peso {pillar['weight']})</span>", unsafe_allow_html=True)
            
            criteria = get_criteria_by_pillar(supabase, pillar['id'])
            if not criteria:
                st.caption("Sem critérios definidos.")
            
            for crit in criteria:
                # Card visual para o critério
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**📊 {crit['name']}**")
                    c2.markdown(f"Tipo: `{crit['criterion_type']}`")
                    
                    thresholds = get_thresholds_by_criterion(supabase, crit['id'])
                    if thresholds:
                        # Visualização de faixas como "Badges" coloridos
                        st.write("Regras de Pontuação:")
                        for th in thresholds:
                            color_map = {
                                "green": "#e6f4ea",
                                "yellow": "#fef7e0",
                                "red": "#fce8e6",
                                "gray": "#f1f3f4"
                            }
                            text_map = {
                                "green": "#137333",
                                "yellow": "#b06000",
                                "red": "#c5221f",
                                "gray": "#5f6368"
                            }
                            
                            bg = color_map.get(th.get('color', 'gray'), "#f1f3f4")
                            txt = text_map.get(th.get('color', 'gray'), "#333")
                            
                            st.markdown(
                                f"""
                                <div style="background-color: {bg}; color: {txt}; padding: 8px; border-radius: 6px; margin-bottom: 4px; font-size: 0.9em;">
                                    <strong>{th['label']}</strong> ({th['min_value']} a {th['max_value']}) 
                                    <span style="float:right"><b>{th['score']} pts</b></span>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                    else:
                        st.caption("⚠️ Nenhuma faixa de pontuação configurada.")
            
            st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    show_admin_methodology()
