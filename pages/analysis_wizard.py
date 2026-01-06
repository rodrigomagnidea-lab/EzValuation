"""
Página de Análise de Investimentos - VERSÃO RESTAURADA E ESTABILIZADA
Wizard para usuários criarem análises usando a metodologia ativa.
"""
import streamlit as st
from datetime import datetime
from utils.db import (
    get_supabase_client,
    get_active_methodology,
    get_full_methodology_tree,
    create_analysis,
    update_analysis,
    get_user_analyses,
    get_analysis_by_id
)
# Nota: Certifique-se de que o arquivo utils/valuation.py existe com estas funções.
# Se não existir, comente as linhas abaixo para o app carregar.
try:
    from utils.valuation import (
        get_fii_data,
        evaluate_criterion_value,
        calculate_weighted_score,
        gordon_growth_model,
        ipca_plus_valuation,
        get_market_index_value
    )
except ImportError:
    # Fallback caso o arquivo de valuation não exista
    def get_fii_data(ticker): return {"name": ticker, "price": 100.0}
    def get_market_index_value(sb, name, default): return default
    def evaluate_criterion_value(val, ranges): return None
    pass

from fpdf import FPDF
import json

def show_analysis_wizard():
    """Função principal da página de análise."""
    
    # Renderiza sidebar centralizada (mantém navegação consistente)
    from utils.sidebar import show_sidebar
    show_sidebar()
    
    # OBS: Não fazemos check_authentication aqui pois o app.py já garante isso.
    # Isso evita o looping infinito.

    st.title("📊 Análise de Investimentos")
    st.markdown("---")
    
    # Tenta conectar
    try:
        supabase = get_supabase_client()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📝 Nova Análise", "📂 Minhas Análises", "💰 Valuation"])
    
    with tab1:
        new_analysis_tab(supabase)
    
    with tab2:
        my_analyses_tab(supabase)
    
    with tab3:
        valuation_tab(supabase)


def new_analysis_tab(supabase):
    """Tab para criar uma nova análise."""
    
    st.subheader("📝 Nova Análise de FII")
    
    # Verificar se existe metodologia ativa com tratamento de erro
    try:
        active_methodology = get_active_methodology(supabase)
    except Exception:
        st.warning("Erro ao buscar metodologia ativa.")
        return

    if not active_methodology:
        st.info("ℹ️ Nenhuma metodologia ativa encontrada. Entre em contato com o administrador.")
        return
    
    # CORREÇÃO DEFENSIVA: Usa .get() para evitar KeyError (Critical Fix)
    met_name = active_methodology.get('name') or active_methodology.get('version') or active_methodology.get('Name') or "Sem Nome"
    st.success(f"✅ Usando metodologia: **{met_name}**")
    
    # Setup inicial
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input(
            "Ticker do FII",
            placeholder="Ex: HGLG11",
            help="Digite o código do fundo imobiliário"
        ).upper()
    
    with col2:
        segment = st.selectbox(
            "Segmento",
            options=[
                'Logístico / Industrial',
                'Lajes Corporativas',
                'Shopping',
                'Educacional',
                'Saúde / BTS'
            ]
        )
    
    if not ticker:
        st.info("👆 Digite o ticker para começar a análise.")
        return
    
    # Buscar dados do FII
    with st.spinner("Buscando dados do FII..."):
        try:
            fii_data = get_fii_data(ticker)
        except:
            fii_data = None
    
    if fii_data:
        st.success(f"✅ {fii_data.get('name', ticker)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Preço Atual", f"R$ {fii_data.get('price', 0):.2f}")
        with col2:
            dy = fii_data.get('dividend_yield', 0) or 0
            st.metric("Dividend Yield", f"{dy * 100:.2f}%")
        with col3:
            vol = fii_data.get('volume', 0) or 0
            st.metric("Volume", f"{vol:,.0f}")
    else:
        st.warning("⚠️ Não foi possível buscar dados automáticos. Continuando análise manual...")
        fii_data = {'name': ticker, 'price': 0.0}
    
    st.markdown("---")
    
    # Carregar metodologia completa
    # CORREÇÃO DEFENSIVA: Valida que temos ID antes de buscar
    met_id = active_methodology.get('id') or active_methodology.get('ID')
    if not met_id:
        st.error("❌ Erro de dados: Metodologia sem ID válido.")
        return
    
    tree = get_full_methodology_tree(supabase, met_id)
    
    # Ajuste: se tree for uma lista (retorno do db.py atual), pegamos a estrutura
    # O db.py atual retorna uma lista de pilares. O código antigo esperava um dict {'pillars': [...]}.
    # Vamos adaptar:
    if isinstance(tree, list):
        pillars_list = tree
    elif isinstance(tree, dict):
        pillars_list = tree.get('pillars', [])
    else:
        pillars_list = []

    if not pillars_list:
        st.warning("⚠️ Esta metodologia ainda não tem pilares configurados.")
        return
    
    # Inicializar session state para armazenar inputs
    if 'analysis_inputs' not in st.session_state:
        st.session_state.analysis_inputs = {}
    
    if 'analysis_overrides' not in st.session_state:
        st.session_state.analysis_overrides = {}
    
    # Renderizar formulário dinâmico
    st.subheader("📋 Checklist de Avaliação")
    
    total_score = 0
    total_weight = 0
    results_by_pillar = {}
    
    for pillar in pillars_list:
        # Garante nome do pilar
        p_name = pillar.get('name') or pillar.get('display_name') or "Pilar"
        p_weight = float(pillar.get('weight', 1))
        
        with st.expander(f"🏛️ {p_name} (Peso: {p_weight})", expanded=True):
            
            if pillar.get('description'):
                st.info(pillar['description'])
            
            criteria_list = pillar.get('criteria', [])
            if not criteria_list:
                st.caption("Nenhum critério configurado neste pilar.")
                continue
            
            pillar_results = []
            
            for criterion in criteria_list:
                c_name = criterion.get('name') or criterion.get('display_name') or "Critério"
                c_id = criterion['id']
                
                st.markdown(f"**📊 {c_name}**")
                
                if criterion.get('rule_description'):
                    st.caption(f"📏 {criterion['rule_description']}")
                
                # Renderizar input (Simplificado para evitar erro se 'type' não existir)
                # Assume numérico/range se type não for especificado
                criterion['type'] = criterion.get('type', 'numeric') 
                input_value = render_criterion_input(criterion, ticker)
                
                # Lógica de Avaliação Automática vs Manual
                evaluated_range = None
                
                # Se tiver faixas (thresholds/ranges)
                # O db.py retorna 'thresholds', o código antigo usava 'ranges'. Vamos normalizar.
                ranges = criterion.get('thresholds') or criterion.get('ranges') or []
                
                if input_value is not None and ranges:
                    # Tenta avaliar automaticamente se utils.valuation estiver ativo
                    try:
                        evaluated_range = evaluate_criterion_value(input_value, ranges)
                    except:
                        evaluated_range = None
                    
                    if evaluated_range:
                        # Exibe resultado automático
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            color_map = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
                            emoji = color_map.get(evaluated_range.get('color'), "⚪")
                            st.success(f"{emoji} **{evaluated_range['label']}** - {evaluated_range['score']} pts")
                        
                        with col2:
                            if st.button("✏️ Editar", key=f"ovr_{c_id}"):
                                st.session_state.analysis_overrides[c_id] = True
                        
                        # Se override ativo ou sem avaliação automática
                        if st.session_state.analysis_overrides.get(c_id, False):
                            range_opts = {f"{r['label']} ({r['score']} pts)": r for r in ranges}
                            sel = st.selectbox("Ajuste Manual:", list(range_opts.keys()), key=f"sel_man_{c_id}")
                            evaluated_range = range_opts[sel]
                            
                        pillar_results.append({
                            'criterion': c_name,
                            'value': input_value,
                            'points': evaluated_range['score']
                        })
                    else:
                        # Caso não consiga avaliar (ex: valor fora da faixa), pede manual
                        range_opts = {f"{r['label']} ({r['score']} pts)": r for r in ranges}
                        sel = st.selectbox("Selecione a Classificação:", list(range_opts.keys()), key=f"sel_dir_{c_id}")
                        sel_range = range_opts[sel]
                        pillar_results.append({
                            'criterion': c_name,
                            'value': input_value,
                            'points': sel_range['score']
                        })

                else:
                    # Sem faixas: Input direto de pontos se não for automático
                    # fallback simples
                    points = st.slider("Pontuação (0-10)", 0.0, 10.0, step=0.5, key=f"slider_{c_id}")
                    pillar_results.append({
                        'criterion': c_name,
                        'value': points,
                        'points': points
                    })
                
                st.markdown("---")
            
            # Calcular score do pilar
            if pillar_results:
                p_score = sum(r['points'] for r in pillar_results) / len(pillar_results)
                w_score = p_score * p_weight
                
                total_score += w_score
                total_weight += p_weight
                
                results_by_pillar[p_name] = {
                    'score': p_score,
                    'weight': p_weight,
                    'weighted_score': w_score,
                    'criteria_results': pillar_results
                }
                
                st.metric(f"Score do Pilar: {p_name}", f"{p_score:.2f} pts")
    
    # Score Final
    if total_weight > 0:
        final_score = total_score / total_weight
        
        st.markdown("---")
        st.subheader("🎯 Resultado Final")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score Total", f"{final_score:.2f}")
        with col2:
            st.metric("Peso Total", f"{total_weight:.1f}")
        with col3:
            classification = classify_score(final_score)
            st.metric("Classificação", classification)
        
        # Salvar
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            save_status = st.selectbox("Status", options=['draft', 'completed'], index=1)
        
        with col2:
            if st.button("💾 Salvar Análise", type="primary", use_container_width=True):
                # Recupera ID do usuário de forma segura
                user_id = st.session_state.user.user.id if hasattr(st.session_state.user, 'user') else st.session_state.user.id
                
                analysis_data_pack = {
                    'final_score': final_score,
                    'classification': classification,
                    'by_pillar': results_by_pillar,
                    'fii_data': fii_data
                }
                
                # Tenta salvar
                try:
                    create_analysis(
                        supabase,
                        user_id,
                        ticker,
                        segment,
                        st.session_state.analysis_inputs,
                        analysis_data_pack,
                        save_status
                    )
                    st.success("✅ Análise salva com sucesso!")
                    st.balloons()
                    # Limpa
                    st.session_state.analysis_inputs = {}
                    st.session_state.analysis_overrides = {}
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")


def render_criterion_input(criterion, ticker):
    """Renderiza o input apropriado baseado no tipo do critério."""
    c_type = criterion.get('type', 'numeric')
    c_id = criterion['id']
    key = f"input_{c_id}"
    
    if c_type == 'numeric':
        unit = criterion.get('unit', '')
        val = st.number_input(f"Valor {unit}", value=0.0, step=0.1, key=key)
        return val
    elif c_type == 'boolean':
        return st.toggle("Atende ao critério?", key=key)
    
    # Fallback para texto/numérico genérico
    return st.number_input("Valor", value=0.0, key=key)


def classify_score(score):
    if score >= 8: return "🟢 Excelente"
    elif score >= 6: return "🟡 Bom"
    elif score >= 4: return "🟠 Médio"
    else: return "🔴 Fraco"


def my_analyses_tab(supabase):
    st.subheader("📂 Minhas Análises")
    try:
        # Tenta pegar ID do usuário
        uid = st.session_state.user.user.id if hasattr(st.session_state.user, 'user') else st.session_state.user.id
        analyses = get_user_analyses(supabase, uid)
    except:
        st.error("Erro ao carregar análises.")
        return

    if not analyses:
        st.info("Nenhuma análise salva.")
        return

    for ana in analyses:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"**{ana['ticker']}** ({ana['segment']})")
                st.caption(f"Data: {ana.get('created_at', '')[:10]}")
            with c2:
                res = ana.get('results', {})
                score = res.get('final_score', 0) if isinstance(res, dict) else 0
                st.metric("Score", f"{score:.2f}")
            with c3:
                st.write(f"Status: {ana['status']}")
            
            # PDF Generation Button (Simulado se fpdf falhar)
            if st.button("📄 PDF", key=f"pdf_{ana['id']}"):
                path = generate_pdf_report(ana)
                if path:
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download", f, file_name=f"{ana['ticker']}.pdf")


def valuation_tab(supabase):
    st.subheader("💰 Calculadora Rápida")
    st.info("Funcionalidade simplificada para validação.")
    
    c1, c2 = st.columns(2)
    div = c1.number_input("Dividendo Mensal (R$)", 1.0, step=0.01)
    rate = c2.number_input("Taxa de Desconto Anual (%)", 10.0, step=0.5)
    
    if st.button("Calcular Gordon Simples"):
        try:
            val = (div * 12) / (rate / 100)
            st.success(f"Valor Justo (Gordon): R$ {val:.2f}")
        except:
            st.error("Erro no cálculo.")


def generate_pdf_report(analysis):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Analise: {analysis['ticker']}", ln=True)
        pdf.output("/tmp/report.pdf")
        return "/tmp/report.pdf"
    except:
        st.warning("Biblioteca FPDF não configurada ou erro ao gerar.")
        return None

if __name__ == "__main__":
    # Bloco de teste local apenas - não executa no import do app.py
    pass
