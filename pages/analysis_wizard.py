import streamlit as st
import time
from utils.db import (
    get_supabase_client,
    get_active_methodology,
    get_full_methodology_tree
)

def show_analysis_wizard():
    st.title("🧙 Assistente de Valuation")

    # 1. Conexão
    try:
        supabase = get_supabase_client()
    except Exception as e:
        st.error("Erro de conexão com banco de dados.")
        return

    # 2. Buscar Metodologia Ativa
    methodology = get_active_methodology(supabase)
    
    # --- ÁREA DE DIAGNÓSTICO (Sempre visível para debug) ---
    with st.expander("🕵️ Debug: Dados Brutos da Metodologia"):
        st.json(methodology if methodology else {"status": "Nenhuma metodologia encontrada"})
        st.caption("Use isto para diagnosticar problemas de estrutura de dados.")
    # -------------------------------------------------------

    # Valida se metodologia existe
    if not methodology:
        st.info("ℹ️ Nenhuma metodologia ativa encontrada.")
        st.markdown("Para começar, vá no menu **🔧 Admin: Metodologias** e crie sua primeira metodologia.")
        return

    # DEFENSIVO: Usa .get() para evitar KeyError se o campo 'name' não existir
    # Tenta 'name' e 'Name' (case variations) e fallback para "Sem Nome"
    met_name = methodology.get('name') or methodology.get('Name') or "Sem Nome (Verifique estrutura do DB)"
    st.markdown(f"**Metodologia Ativa:** `{met_name}`")
    st.markdown("---")

    # 3. Buscar Árvore Completa (Pilar -> Critério -> Faixas)
    # DEFENSIVO: Valida que temos um ID antes de buscar
    met_id = methodology.get('id') or methodology.get('ID')
    
    if not met_id:
        st.error("❌ **Erro Crítico:** Metodologia sem ID.")
        st.warning("A metodologia existe no banco, mas não possui um campo 'id'. Verifique a estrutura da tabela.")
        st.stop()
        return

    pillars = get_full_methodology_tree(supabase, met_id)
    
    if not pillars:
        st.warning("Esta metodologia existe, mas ainda não tem pilares/critérios definidos.")
        return

    # 4. Formulário de Avaliação
    with st.form("valuation_form"):
        st.subheader("📝 Checklist de Avaliação")
        scores = {}
        
        for pillar in pillars:
            with st.container(border=True):
                st.markdown(f"### 🏛️ {pillar.get('name', 'Pilar sem nome')}")
                
                # Se não tiver critérios, avisa
                if not pillar.get('criteria'):
                    st.caption("Sem critérios neste pilar.")
                    continue

                for crit in pillar['criteria']:
                    cid = crit['id']
                    crit_name = crit.get('name', 'Critério sem nome')
                    
                    st.markdown(f"**📊 {crit_name}**")
                    
                    # Verifica se existem faixas (thresholds)
                    thresholds = crit.get('thresholds', [])
                    
                    if thresholds:
                        # Ordena opções
                        options_map = {f"{t['label']} ({t['score']} pts)": t['score'] for t in thresholds}
                        
                        selected_label = st.selectbox(
                            "Classificação:",
                            options=list(options_map.keys()),
                            key=f"sel_{cid}",
                            label_visibility="collapsed"
                        )
                        scores[cid] = options_map[selected_label]
                    else:
                        # Input numérico livre
                        scores[cid] = st.number_input(
                            "Pontuação (0-10)", 
                            min_value=0.0, 
                            max_value=10.0, 
                            step=0.5,
                            key=f"num_{cid}"
                        )
                    
                    st.caption("---")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de Envio
        submitted = st.form_submit_button("✅ Gerar Resultado", type="primary", use_container_width=True)
        
        if submitted:
            st.success("Cálculo realizado!")
            st.json(scores)

if __name__ == "__main__":
    show_analysis_wizard()
