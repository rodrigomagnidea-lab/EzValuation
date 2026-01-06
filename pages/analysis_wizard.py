"""
Página de Análise de Investimentos
Wizard para usuários criarem análises usando a metodologia ativa.
"""
import streamlit as st
from datetime import datetime
from utils.auth import check_authentication
from utils.db import (
    get_supabase_client,
    get_active_methodology,
    get_full_methodology_tree,
    create_analysis,
    update_analysis,
    get_user_analyses,
    get_analysis_by_id
)
from utils.valuation import (
    get_fii_data,
    evaluate_criterion_value,
    calculate_weighted_score,
    gordon_growth_model,
    ipca_plus_valuation
)
from fpdf import FPDF
import json


def main():
    """Função principal da página de análise."""
    if not check_authentication():
        st.error("❌ Você precisa estar autenticado para acessar esta página.")
        st.stop()
        return
    
    st.title("📊 Análise de Investimentos")
    st.markdown("---")
    
    supabase = get_supabase_client()
    
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
    
    # Verificar se existe metodologia ativa
    active_methodology = get_active_methodology(supabase)
    
    if not active_methodology:
        st.error("⚠️ Nenhuma metodologia ativa encontrada. Entre em contato com o administrador.")
        return
    
    st.success(f"✅ Usando metodologia: **{active_methodology['version']}**")
    
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
        fii_data = get_fii_data(ticker)
    
    if fii_data:
        st.success(f"✅ {fii_data['name']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Preço Atual", f"R$ {fii_data['price']:.2f}")
        with col2:
            st.metric("Dividend Yield", f"{fii_data.get('dividend_yield', 0) * 100:.2f}%")
        with col3:
            st.metric("Volume", f"{fii_data.get('volume', 0):,.0f}")
    else:
        st.warning("⚠️ Não foi possível buscar dados do FII. Continuando análise manual...")
    
    st.markdown("---")
    
    # Carregar metodologia completa
    tree = get_full_methodology_tree(supabase, active_methodology['id'])
    
    if not tree or not tree.get('pillars'):
        st.error("❌ Metodologia sem pilares configurados.")
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
    
    for pillar in tree['pillars']:
        with st.expander(f"🏛️ {pillar['name']} (Peso: {pillar['weight']})", expanded=True):
            
            if pillar.get('description'):
                st.info(pillar['description'])
            
            if not pillar.get('criteria'):
                st.warning("Nenhum critério configurado neste pilar.")
                continue
            
            pillar_results = []
            
            for criterion in pillar['criteria']:
                st.markdown(f"**📊 {criterion['name']}**")
                
                if criterion.get('rule_description'):
                    st.caption(f"📏 {criterion['rule_description']}")
                
                # Renderizar input baseado no tipo
                input_value = render_criterion_input(criterion, ticker)
                
                # Avaliar automaticamente
                if input_value is not None and criterion.get('ranges'):
                    evaluated_range = evaluate_criterion_value(input_value, criterion['ranges'])
                    
                    if evaluated_range:
                        # Permitir override manual
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            color_emoji = {
                                "green": "🟢",
                                "yellow": "🟡",
                                "red": "🔴"
                            }.get(evaluated_range['color'], "⚪")
                            
                            st.success(
                                f"{color_emoji} **{evaluated_range['label']}** - "
                                f"{evaluated_range['points']} pontos ({evaluated_range['impact']})"
                            )
                        
                        with col2:
                            override_key = f"override_{criterion['id']}"
                            
                            if st.button("✏️ Override", key=override_key):
                                st.session_state.analysis_overrides[criterion['id']] = True
                        
                        # Se override ativo, permitir seleção manual
                        if st.session_state.analysis_overrides.get(criterion['id'], False):
                            range_options = {r['label']: r for r in criterion['ranges']}
                            
                            selected_label = st.selectbox(
                                "Escolha a faixa manualmente:",
                                options=list(range_options.keys()),
                                key=f"manual_range_{criterion['id']}"
                            )
                            
                            evaluated_range = range_options[selected_label]
                        
                        pillar_results.append({
                            'criterion': criterion['name'],
                            'value': input_value,
                            'range': evaluated_range,
                            'points': evaluated_range['points']
                        })
                    else:
                        st.warning("⚠️ Valor fora das faixas definidas.")
                
                st.markdown("---")
            
            # Calcular score do pilar
            if pillar_results:
                pillar_score = sum(r['points'] for r in pillar_results) / len(pillar_results)
                weighted_pillar_score = pillar_score * float(pillar['weight'])
                
                total_score += weighted_pillar_score
                total_weight += float(pillar['weight'])
                
                results_by_pillar[pillar['name']] = {
                    'score': pillar_score,
                    'weight': pillar['weight'],
                    'weighted_score': weighted_pillar_score,
                    'criteria_results': pillar_results
                }
                
                st.metric(
                    f"Score do Pilar: {pillar['name']}",
                    f"{pillar_score:.2f} pts (Ponderado: {weighted_pillar_score:.2f})"
                )
    
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
        
        # Salvar análise
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            save_status = st.selectbox("Status", options=['draft', 'completed'], index=1)
        
        with col2:
            if st.button("💾 Salvar Análise", type="primary"):
                user_id = st.session_state.user.user.id
                
                analysis_data = {
                    'user_id': user_id,
                    'ticker': ticker,
                    'segment': segment,
                    'status': save_status,
                    'inputs': st.session_state.analysis_inputs,
                    'results': {
                        'final_score': final_score,
                        'classification': classification,
                        'by_pillar': results_by_pillar,
                        'fii_data': fii_data
                    }
                }
                
                result = create_analysis(
                    supabase,
                    user_id,
                    ticker,
                    segment,
                    st.session_state.analysis_inputs,
                    analysis_data['results'],
                    save_status
                )
                
                if result:
                    st.success("✅ Análise salva com sucesso!")
                    
                    # Limpar session state
                    st.session_state.analysis_inputs = {}
                    st.session_state.analysis_overrides = {}
                    
                    st.balloons()


def render_criterion_input(criterion, ticker):
    """Renderiza o input apropriado baseado no tipo do critério."""
    
    criterion_type = criterion['type']
    criterion_id = criterion['id']
    key = f"input_{criterion_id}"
    
    if criterion_type == 'numeric':
        value = st.number_input(
            f"Valor ({criterion.get('unit', '')})",
            value=st.session_state.analysis_inputs.get(key, 0.0),
            key=key,
            step=0.1
        )
        st.session_state.analysis_inputs[key] = value
        return value
    
    elif criterion_type == 'percent':
        value = st.number_input(
            "Valor (%)",
            value=st.session_state.analysis_inputs.get(key, 0.0),
            key=key,
            min_value=0.0,
            max_value=100.0,
            step=0.1
        )
        st.session_state.analysis_inputs[key] = value
        return value
    
    elif criterion_type == 'boolean':
        value = st.radio(
            "Resposta",
            options=[True, False],
            format_func=lambda x: "Sim" if x else "Não",
            key=key,
            horizontal=True
        )
        st.session_state.analysis_inputs[key] = value
        return value
    
    elif criterion_type == 'categorical':
        # Extrair opções das ranges
        if criterion.get('ranges'):
            options = [r['label'] for r in criterion['ranges']]
            value = st.selectbox(
                "Selecione",
                options=options,
                key=key
            )
            st.session_state.analysis_inputs[key] = value
            return value
        else:
            value = st.text_input("Valor", key=key)
            st.session_state.analysis_inputs[key] = value
            return value
    
    return None


def classify_score(score):
    """Classifica o score em categorias."""
    if score >= 8:
        return "🟢 Excelente"
    elif score >= 6:
        return "🟡 Bom"
    elif score >= 4:
        return "🟠 Médio"
    else:
        return "🔴 Fraco"


def my_analyses_tab(supabase):
    """Tab para visualizar análises salvas."""
    
    st.subheader("📂 Minhas Análises")
    
    user_id = st.session_state.user.user.id
    analyses = get_user_analyses(supabase, user_id)
    
    if not analyses:
        st.info("Você ainda não criou nenhuma análise.")
        return
    
    # Exibir análises como cards
    for analysis in analyses:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"### {analysis['ticker']}")
                st.caption(f"Segmento: {analysis['segment']}")
            
            with col2:
                status_emoji = "✅" if analysis['status'] == 'completed' else "📝"
                st.metric("Status", f"{status_emoji} {analysis['status']}")
            
            with col3:
                results = analysis.get('results', {})
                final_score = results.get('final_score', 0)
                st.metric("Score", f"{final_score:.2f}")
            
            with col4:
                created = analysis.get('created_at', '')
                if created:
                    date = created.split('T')[0]
                    st.caption(f"Criado em:\n{date}")
            
            # Detalhes expandíveis
            with st.expander("Ver Detalhes"):
                results = analysis.get('results', {})
                
                st.markdown(f"**Classificação:** {results.get('classification', 'N/A')}")
                
                # Score por pilar
                if 'by_pillar' in results:
                    st.markdown("#### Score por Pilar")
                    
                    for pillar_name, pillar_data in results['by_pillar'].items():
                        st.markdown(
                            f"**{pillar_name}**: {pillar_data['score']:.2f} pts "
                            f"(Peso: {pillar_data['weight']}) = {pillar_data['weighted_score']:.2f}"
                        )
                
                # Botão para exportar PDF
                if st.button(f"📄 Exportar PDF", key=f"export_{analysis['id']}"):
                    pdf_path = generate_pdf_report(analysis)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                "⬇️ Baixar PDF",
                                f,
                                file_name=f"analise_{analysis['ticker']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf"
                            )
            
            st.markdown("---")


def valuation_tab(supabase):
    """Tab para cálculos de valuation."""
    
    st.subheader("💰 Calculadora de Valuation")
    
    st.markdown("### Modelo Gordon (Perpetuidade)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dividend = st.number_input("Dividendo Mensal (R$)", value=1.0, step=0.01, key="gordon_div")
    with col2:
        growth = st.number_input("Taxa Crescimento (%)", value=3.0, step=0.1, key="gordon_growth") / 100
    with col3:
        discount = st.number_input("Taxa Desconto (%)", value=10.0, step=0.1, key="gordon_discount") / 100
    
    if st.button("Calcular Gordon", key="calc_gordon"):
        try:
            annual_div = dividend * 12
            fair_value = gordon_growth_model(annual_div, growth, discount)
            st.success(f"✅ Valor Justo: **R$ {fair_value:.2f}** por cota")
        except ValueError as e:
            st.error(str(e))
    
    st.markdown("---")
    
    # IPCA+ Valuation
    st.markdown("### Modelo IPCA+")
    
    active_methodology = get_active_methodology(supabase)
    
    if active_methodology:
        indices = active_methodology.get('indices', {})
        default_ipca = indices.get('ipca', 0.045) * 100
        default_ntnb = indices.get('ntnbReal', 0.06) * 100
    else:
        default_ipca = 4.5
        default_ntnb = 6.0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ipca_div = st.number_input("Dividendo Mensal (R$)", value=1.0, step=0.01, key="ipca_div")
    with col2:
        ipca_rate = st.number_input("IPCA (%)", value=default_ipca, step=0.1, key="ipca_rate") / 100
    with col3:
        premium = st.number_input("Prêmio sobre IPCA (%)", value=default_ntnb, step=0.1, key="premium") / 100
    
    if st.button("Calcular IPCA+", key="calc_ipca"):
        result = ipca_plus_valuation(ipca_div, ipca_rate, premium, years=10)
        
        st.success(f"✅ Valor Justo: **R$ {result['fair_value']:.2f}** por cota")
        st.info(f"Retorno Anual Esperado: {result['annual_return'] * 100:.2f}%")
        
        # Gráfico de dividendos projetados
        import plotly.graph_objects as go
        
        years = list(range(1, 11))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=years,
            y=result['projected_dividends'],
            name='Dividendos Projetados'
        ))
        
        fig.update_layout(
            title="Projeção de Dividendos (10 anos)",
            xaxis_title="Ano",
            yaxis_title="Dividendo Anual (R$)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def generate_pdf_report(analysis):
    """Gera relatório em PDF da análise."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Título
        pdf.cell(0, 10, f"Análise de Investimento - {analysis['ticker']}", ln=True, align="C")
        pdf.ln(5)
        
        # Informações básicas
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Segmento: {analysis['segment']}", ln=True)
        pdf.cell(0, 10, f"Status: {analysis['status']}", ln=True)
        pdf.cell(0, 10, f"Data: {analysis.get('created_at', '').split('T')[0]}", ln=True)
        pdf.ln(5)
        
        # Resultado final
        results = analysis.get('results', {})
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Score Final: {results.get('final_score', 0):.2f}", ln=True)
        pdf.cell(0, 10, f"Classificacao: {results.get('classification', 'N/A')}", ln=True)
        pdf.ln(10)
        
        # Score por pilar
        if 'by_pillar' in results:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Score por Pilar:", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for pillar_name, pillar_data in results['by_pillar'].items():
                pdf.cell(
                    0, 8,
                    f"{pillar_name}: {pillar_data['score']:.2f} pts (Peso: {pillar_data['weight']})",
                    ln=True
                )
        
        # Salvar PDF
        pdf_path = f"/tmp/analise_{analysis['ticker']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(pdf_path)
        
        return pdf_path
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None


if __name__ == "__main__":
    main()
