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
    
    if not methodology:
        st.info("ℹ️ Nenhuma metodologia ativa encontrada.")
        st.markdown("Para começar, vá no menu **🔧 Admin: Metodologias** e crie sua primeira metodologia.")
        return

    st.markdown(f"**Metodologia Ativa:** `{methodology['name']}`")
    st.markdown("---")

    # 3. Buscar Árvore Completa (Pilar -> Critério -> Faixas)
    pillars = get_full_methodology_tree(supabase, methodology['id'])
    
    if not pillars:
        st.warning("Esta metodologia existe, mas ainda não tem pilares/critérios definidos.")
        return

    # 4. Formulário de Avaliação
    with st.form("valuation_form"):
        st.subheader("📝 Checklist de Avaliação")
        scores = {}
        
        for pillar in pillars:
            with st.container(border=True):
                st.markdown(f"### 🏛️ {pillar['name']}")
                
                # Se não tiver critérios, avisa
                if not pillar.get('criteria'):
                    st.caption("Sem critérios neste pilar.")
                    continue

                for crit in pillar['criteria']:
                    # Cria um ID único para o input
                    cid = crit['id']
                    
                    st.markdown(f"**📊 {crit['name']}**")
                    
                    # Verifica se existem faixas (thresholds) para criar um selectbox
                    thresholds = crit.get('thresholds', [])
                    
                    if thresholds:
                        # Ordena as opções (ex: do maior score para o menor)
                        # Cria um dicionário para mapear "Texto do Select" -> "Valor Numérico"
                        options_map = {f"{t['label']} ({t['score']} pts)": t['score'] for t in thresholds}
                        
                        selected_label = st.selectbox(
                            "Classificação:",
                            options=list(options_map.keys()),
                            key=f"sel_{cid}",
                            label_visibility="collapsed"
                        )
                        # Salva a pontuação correspondente
                        scores[cid] = options_map[selected_label]
                    else:
                        # Se não tiver faixas cadastradas, mostra input numérico livre
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
            # Aqui futuramente entra a lógica de salvar no banco 'analysis_data'
            st.json(scores)

if __name__ == "__main__":
    show_analysis_wizard()
