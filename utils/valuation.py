"""
Módulo de Valuation
Implementa modelos financeiros para avaliação de Fundos Imobiliários.
"""
import yfinance as yf
from typing import Optional, Dict
import pandas as pd


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


def ipca_plus_valuation(dividend: float, ipca: float, premium: float, years: int = 10) -> Dict:
    """
    Calcula valuation usando IPCA + spread.
    Desconta dividendos futuros corrigidos pelo IPCA + prêmio.
    
    Args:
        dividend: Dividendo atual mensal
        ipca: Taxa IPCA esperada (decimal, ex: 0.045 para 4.5%)
        premium: Prêmio sobre IPCA (decimal, ex: 0.06 para 6%)
        years: Período de projeção
        
    Returns:
        dict: {
            'fair_value': valor justo por cota,
            'annual_return': retorno anual esperado,
            'projected_dividends': lista de dividendos projetados
        }
    """
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
        'terminal_value': terminal_value
    }


def calculate_ntnb_spread(fii_yield: float, ntnb_yield: float) -> float:
    """
    Calcula o spread entre yield do FII e NTN-B.
    
    Args:
        fii_yield: Dividend yield do FII (decimal)
        ntnb_yield: Yield da NTN-B (decimal)
        
    Returns:
        float: Spread em pontos percentuais
    """
    return (fii_yield - ntnb_yield) * 100


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
