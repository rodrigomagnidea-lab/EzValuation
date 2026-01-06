"""
Módulo de Valuation
Implementa modelos financeiros para avaliação de Fundos Imobiliários.
Índices de mercado são obtidos da tabela global market_indices.
"""
import yfinance as yf
from typing import Optional, Dict
import pandas as pd
import streamlit as st
from supabase import Client


def get_fii_data(ticker: str) -> Optional[Dict]:
    """
    Busca dados de um FII usando yfinance.
    
    Args:
        ticker: Código do ticker (ex: 'HGLG11.SA')
        
    Returns:
        dict com dados do FII ou None se não encontrado
    """
    try:
        # Adicionar .SA se não estiver presente
        if not ticker.endswith('.SA'):
            ticker = f"{ticker}.SA"
        
        fii = yf.Ticker(ticker)
        info = fii.info
        
        return {
            'ticker': ticker,
            'price': info.get('regularMarketPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'market_cap': info.get('marketCap', 0),
            'volume': info.get('volume', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'name': info.get('longName', ticker)
        }
    except Exception as e:
        return None


def get_market_index_value(supabase: Client, index_name: str, default: float = 0.0) -> float:
    """
    Busca o valor de um índice de mercado do banco de dados.
    
    Args:
        supabase: Cliente Supabase
        index_name: Nome do índice (ex: 'IPCA', 'NTN-B', 'CDI')
        default: Valor padrão caso não encontre
        
    Returns:
        float: Valor do índice em formato decimal (ex: 0.045 para 4.5%)
    """
    try:
        response = supabase.table('market_indices')\
            .select('value')\
            .eq('name', index_name)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            # Converter para decimal (dividir por 100 se estiver em %)
            value = float(response.data[0]['value'])
            # Assumir que valores maiores que 1 estão em % e precisam ser convertidos
            return value / 100 if value > 1 else value
        return default
    except Exception as e:
        st.warning(f"Não foi possível buscar índice {index_name}, usando valor padrão {default}")
        return default


def gordon_growth_model(dividend: float, growth_rate: float, discount_rate: float) -> float:
    """
    Modelo de Gordon para valuation de perpetuidade.
    
    Fórmula: P = D / (r - g)
    
    Args:
        dividend: Dividendo anual esperado
        growth_rate: Taxa de crescimento perpétua (decimal, ex: 0.03 para 3%)
        discount_rate: Taxa de desconto exigida (decimal, ex: 0.10 para 10%)
        
    Returns:
        float: Valor justo por cota
    """
    if discount_rate <= growth_rate:
        raise ValueError("Taxa de desconto deve ser maior que taxa de crescimento")
    
    return dividend / (discount_rate - growth_rate)


def fcfe_valuation(fcfe_list: list, discount_rate: float, terminal_growth: float = 0.03) -> float:
    """
    Valuation por Free Cash Flow to Equity (FCFE).
    
    Args:
        fcfe_list: Lista de FCFE projetados (ex: [100, 110, 120])
        discount_rate: Taxa de desconto (WACC ou custo de capital próprio)
        terminal_growth: Taxa de crescimento perpétuo após período projetado
        
    Returns:
        float: Valor presente dos fluxos de caixa
    """
    pv = 0
    
    # Valor presente dos fluxos projetados
    for i, fcfe in enumerate(fcfe_list, start=1):
        pv += fcfe / ((1 + discount_rate) ** i)
    
    # Valor terminal (perpetuidade)
    terminal_fcfe = fcfe_list[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcfe / (discount_rate - terminal_growth)
    
    # Trazer valor terminal a valor presente
    n = len(fcfe_list)
    pv_terminal = terminal_value / ((1 + discount_rate) ** n)
    
    return pv + pv_terminal


def ipca_plus_valuation(supabase: Client, dividend: float, premium: float, years: int = 10) -> Dict:
    """
    Calcula valuation usando IPCA + spread.
    Desconta dividendos futuros corrigidos pelo IPCA + prêmio.
    Busca o valor atual de IPCA do banco de dados.
    
    Args:
        supabase: Cliente Supabase para buscar índices
        dividend: Dividendo atual mensal
        premium: Prêmio sobre IPCA (decimal, ex: 0.06 para 6%)
        years: Período de projeção
        
    Returns:
        dict: {
            'fair_value': valor justo por cota,
            'annual_return': retorno anual esperado,
            'projected_dividends': lista de dividendos projetados,
            'ipca_used': valor do IPCA utilizado
        }
    """
    # Buscar IPCA atual do banco
    ipca = get_market_index_value(supabase, 'IPCA', default=0.045)
    
    discount_rate = ipca + premium
    annual_dividend = dividend * 12
    
    # Projetar dividendos crescendo com IPCA
    projected_dividends = []
    pv_total = 0
    
    for year in range(1, years + 1):
        projected_div = annual_dividend * ((1 + ipca) ** year)
        projected_dividends.append(projected_div)
        pv = projected_div / ((1 + discount_rate) ** year)
        pv_total += pv
    
    # Valor terminal (perpetuidade)
    terminal_dividend = projected_dividends[-1] * (1 + ipca)
    terminal_value = terminal_dividend / (discount_rate - ipca)
    pv_terminal = terminal_value / ((1 + discount_rate) ** years)
    
    fair_value = pv_total + pv_terminal
    
    return {
        'fair_value': fair_value,
        'annual_return': discount_rate,
        'projected_dividends': projected_dividends,
        'terminal_value': terminal_value,
        'ipca_used': ipca
    }


def calculate_ntnb_spread(supabase: Client, fii_yield: float) -> Dict:
    """
    Calcula o spread entre yield do FII e NTN-B.
    Busca o valor atual da NTN-B do banco de dados.
    
    Args:
        supabase: Cliente Supabase para buscar índices
        fii_yield: Dividend yield do FII (decimal)
        
    Returns:
        dict: {
            'spread': spread em pontos percentuais,
            'ntnb_yield': yield da NTN-B utilizado,
            'fii_yield': yield do FII
        }
    """
    ntnb_yield = get_market_index_value(supabase, 'NTN-B', default=0.06)
    
    return {
        'spread': (fii_yield - ntnb_yield) * 100,
        'ntnb_yield': ntnb_yield,
        'fii_yield': fii_yield
    }


def calculate_cap_rate(noi: float, property_value: float) -> float:
    """
    Calcula a taxa de capitalização (Cap Rate).
    
    Cap Rate = NOI / Valor do Imóvel
    
    Args:
        noi: Net Operating Income (receita líquida operacional)
        property_value: Valor do portfólio imobiliário
        
    Returns:
        float: Cap rate (decimal)
    """
    if property_value == 0:
        return 0
    return noi / property_value


def calculate_p_vp(price: float, net_worth_per_share: float) -> float:
    """
    Calcula o índice Preço/Valor Patrimonial.
    
    Args:
        price: Preço da cota
        net_worth_per_share: Valor patrimonial por cota
        
    Returns:
        float: Múltiplo P/VP
    """
    if net_worth_per_share == 0:
        return 0
    return price / net_worth_per_share


def calculate_vacancy_impact(physical_vacancy: float, financial_vacancy: float) -> Dict:
    """
    Calcula o impacto da vacância nos resultados.
    
    Args:
        physical_vacancy: Vacância física (% de área vazia)
        financial_vacancy: Vacância financeira (% de receita não gerada)
        
    Returns:
        dict: análise da vacância
    """
    return {
        'physical_vacancy': physical_vacancy,
        'financial_vacancy': financial_vacancy,
        'spread': financial_vacancy - physical_vacancy,
        'is_healthy': financial_vacancy < 0.10,  # Menos de 10%
        'level': 'low' if financial_vacancy < 0.05 else ('medium' if financial_vacancy < 0.15 else 'high')
    }


def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calcula nota ponderada baseada em scores e pesos.
    
    Args:
        scores: dict com {criterio: pontuacao}
        weights: dict com {criterio: peso}
        
    Returns:
        float: Score ponderado final
    """
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0
    
    weighted_sum = sum(scores.get(k, 0) * weights.get(k, 0) for k in weights.keys())
    return weighted_sum / total_weight


def evaluate_criterion_value(value, ranges: list) -> Optional[Dict]:
    """
    Avalia um valor contra as faixas (ranges) definidas e retorna a faixa correspondente.
    
    Args:
        value: Valor a ser avaliado (pode ser número, string, bool)
        ranges: Lista de dicts com min, max, label, points, color, impact
        
    Returns:
        dict: Faixa correspondente ou None
    """
    try:
        # Se for booleano
        if isinstance(value, bool):
            value_str = 'Sim' if value else 'Não'
            for r in ranges:
                if r.get('label', '').lower() == value_str.lower():
                    return r
        
        # Se for numérico
        elif isinstance(value, (int, float)):
            for r in ranges:
                min_val = float(r['min']) if r['min'] not in [None, '', 'null'] else float('-inf')
                max_val = float(r['max']) if r['max'] not in [None, '', 'null'] else float('inf')
                
                if min_val <= value <= max_val:
                    return r
        
        # Se for categórico (string)
        else:
            value_str = str(value).lower()
            for r in ranges:
                if r.get('label', '').lower() == value_str:
                    return r
        
        return None
    except:
        return None


def get_all_market_indices_for_display(supabase: Client) -> Dict[str, str]:
    """
    Retorna todos os índices formatados para exibição.
    
    Args:
        supabase: Cliente Supabase
        
    Returns:
        dict: {nome: 'valor%'}
    """
    try:
        response = supabase.table('market_indices')\
            .select('name, value, unit')\
            .execute()
        
        if response.data:
            return {
                idx['name']: f"{float(idx['value']):.2f}{idx.get('unit', '%')}"
                for idx in response.data
            }
        return {}
    except:
        return {}
