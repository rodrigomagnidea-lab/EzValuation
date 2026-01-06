"""
Módulo de Banco de Dados - VERSÃO COMPLETA RESTAURADA
Gerencia conexão com Supabase e operações CRUD nas tabelas.
"""
import streamlit as st
from supabase import create_client, Client
from typing import List, Dict, Optional

# ==================== CONEXÃO ====================

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Conecta ao Supabase com fallback para diferentes formatos de secrets.
    Tenta: st.secrets["supabase"]["url"] OU st.secrets["SUPABASE_URL"]
    """
    try:
        # Tenta formato aninhado primeiro
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        # Fallback para formato flat (Streamlit Cloud)
        elif "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        else:
            st.error("❌ Credenciais do Supabase não encontradas em secrets.toml")
            st.info("Configure: supabase.url e supabase.key OU SUPABASE_URL e SUPABASE_KEY")
            st.stop()
        
        return create_client(url, key)
    except KeyError as e:
        st.error(f"❌ Erro ao ler secrets: {e}")
        st.caption("Verifique se secrets.toml está configurado corretamente.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro de conexão com Supabase: {e}")
        st.stop()


# ==================== METHODOLOGY ====================

def get_active_methodology(supabase: Client) -> Optional[Dict]:
    """
    Busca a metodologia marcada como ativa (ou a última criada).
    Retorna None se não houver metodologias ou ocorrer erro.
    """
    try:
        res = supabase.table("methodology_config").select("*").order("created_at", desc=True).limit(1).execute()
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        else:
            return None
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar metodologia: {e}")
        return None


def get_all_methodologies(supabase: Client) -> List[Dict]:
    """Retorna todas as metodologias."""
    try:
        response = supabase.table('methodology_config').select('*').order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar metodologias: {str(e)}")
        return []


def get_methodologies(supabase: Client) -> List[Dict]:
    """Alias para get_all_methodologies (compatibilidade)."""
    return get_all_methodologies(supabase)


def create_methodology(supabase: Client, version: str) -> Optional[Dict]:
    """Cria uma nova metodologia."""
    try:
        response = supabase.table('methodology_config').insert({
            'version': version,
            'is_active': False
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao criar metodologia: {str(e)}")
        return None


def set_active_methodology(supabase: Client, methodology_id: str):
    """Define uma metodologia como ativa e desativa as outras."""
    try:
        # Desativar todas
        supabase.table('methodology_config').update({'is_active': False}).neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Ativar a selecionada
        supabase.table('methodology_config').update({'is_active': True}).eq('id', methodology_id).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao ativar metodologia: {str(e)}")
        return False


# ==================== MARKET INDICES ====================

def get_market_indices(supabase: Client) -> List[Dict]:
    """Retorna todos os índices de mercado cadastrados."""
    try:
        response = supabase.table('market_indices').select('*').order('name').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar índices de mercado: {str(e)}")
        return []


def get_market_index_by_name(supabase: Client, name: str) -> Optional[Dict]:
    """Retorna um índice específico pelo nome."""
    try:
        response = supabase.table('market_indices').select('*').eq('name', name).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao buscar índice {name}: {str(e)}")
        return None


def update_market_index(supabase: Client, index_id: str, new_value: float) -> Optional[Dict]:
    """Atualiza o valor de um índice de mercado."""
    try:
        response = supabase.table('market_indices').update({'value': new_value}).eq('id', index_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao atualizar índice: {str(e)}")
        return None


# ==================== PILLARS ====================

def get_pillars_by_methodology(supabase: Client, methodology_id: str) -> List[Dict]:
    """Retorna todos os pilares de uma metodologia."""
    try:
        response = supabase.table('pillar_config').select('*').eq('methodology_id', methodology_id).order('created_at').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar pilares: {str(e)}")
        return []


def create_pillar(supabase: Client, methodology_id: str, name: str, weight: float, description: str = '') -> Optional[Dict]:
    """Cria um novo pilar."""
    try:
        response = supabase.table('pillar_config').insert({
            'methodology_id': methodology_id,
            'name': name,
            'weight': weight,
            'description': description
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao criar pilar: {str(e)}")
        return None


def update_pillar(supabase: Client, pillar_id: str, name: str, weight: float, description: str):
    """Atualiza um pilar existente."""
    try:
        response = supabase.table('pillar_config').update({
            'name': name,
            'weight': weight,
            'description': description
        }).eq('id', pillar_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao atualizar pilar: {str(e)}")
        return None


def delete_pillar(supabase: Client, pillar_id: str):
    """Deleta um pilar (cascade deleta critérios e ranges)."""
    try:
        supabase.table('pillar_config').delete().eq('id', pillar_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar pilar: {str(e)}")
        return False


# ==================== CRITERIA ====================

def get_criteria_by_pillar(supabase: Client, pillar_id: str) -> List[Dict]:
    """Retorna todos os critérios de um pilar."""
    try:
        response = supabase.table('criterion_config').select('*').eq('pillar_id', pillar_id).order('created_at').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar critérios: {str(e)}")
        return []


def create_criterion(supabase: Client, pillar_id: str, name: str, criterion_type: str, unit: str = '', rule_description: str = '') -> Optional[Dict]:
    """Cria um novo critério."""
    try:
        response = supabase.table('criterion_config').insert({
            'pillar_id': pillar_id,
            'name': name,
            'type': criterion_type,
            'unit': unit,
            'rule_description': rule_description
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao criar critério: {str(e)}")
        return None


def update_criterion(supabase: Client, criterion_id: str, name: str, criterion_type: str, unit: str, rule_description: str):
    """Atualiza um critério existente."""
    try:
        response = supabase.table('criterion_config').update({
            'name': name,
            'type': criterion_type,
            'unit': unit,
            'rule_description': rule_description
        }).eq('id', criterion_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao atualizar critério: {str(e)}")
        return None


def delete_criterion(supabase: Client, criterion_id: str):
    """Deleta um critério (cascade deleta ranges)."""
    try:
        supabase.table('criterion_config').delete().eq('id', criterion_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar critério: {str(e)}")
        return False


# ==================== THRESHOLD RANGES ====================

def get_ranges_by_criterion(supabase: Client, criterion_id: str) -> List[Dict]:
    """Retorna todas as faixas de um critério."""
    try:
        response = supabase.table('threshold_range').select('*').eq('criterion_id', criterion_id).order('points', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar faixas: {str(e)}")
        return []


def get_thresholds_by_criterion(supabase: Client, criterion_id: str) -> List[Dict]:
    """Alias para get_ranges_by_criterion (compatibilidade)."""
    return get_ranges_by_criterion(supabase, criterion_id)


def create_range(supabase: Client, criterion_id: str, min_val: Optional[str], max_val: Optional[str],
                 label: str, points: float, color: str, impact: str) -> Optional[Dict]:
    """Cria uma nova faixa."""
    try:
        response = supabase.table('threshold_range').insert({
            'criterion_id': criterion_id,
            'min': min_val,
            'max': max_val,
            'label': label,
            'points': points,
            'color': color,
            'impact': impact
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao criar faixa: {str(e)}")
        return None


def delete_range(supabase: Client, range_id: str):
    """Deleta uma faixa."""
    try:
        supabase.table('threshold_range').delete().eq('id', range_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar faixa: {str(e)}")
        return False


# ==================== ANALYSIS ====================

def get_user_analyses(supabase: Client, user_id: str) -> List[Dict]:
    """Retorna todas as análises de um usuário."""
    try:
        response = supabase.table('analysis_data').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar análises: {str(e)}")
        return []


def create_analysis(supabase: Client, user_id: str, ticker: str, segment: str,
                    inputs: dict, results: dict, status: str = 'draft') -> Optional[Dict]:
    """Cria uma nova análise."""
    try:
        response = supabase.table('analysis_data').insert({
            'user_id': user_id,
            'ticker': ticker,
            'segment': segment,
            'status': status,
            'inputs': inputs,
            'results': results
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao criar análise: {str(e)}")
        return None


def update_analysis(supabase: Client, analysis_id: str, inputs: dict, results: dict, status: str):
    """Atualiza uma análise existente."""
    try:
        response = supabase.table('analysis_data').update({
            'inputs': inputs,
            'results': results,
            'status': status
        }).eq('id', analysis_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao atualizar análise: {str(e)}")
        return None


def get_analysis_by_id(supabase: Client, analysis_id: str) -> Optional[Dict]:
    """Retorna uma análise específica."""
    try:
        response = supabase.table('analysis_data').select('*').eq('id', analysis_id).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao buscar análise: {str(e)}")
        return None


# ==================== FULL METHODOLOGY TREE ====================

def get_full_methodology_tree(supabase: Client, methodology_id: str) -> Dict:
    """
    Retorna a estrutura completa de uma metodologia:
    Methodology -> Pillars -> Criteria -> Ranges
    """
    try:
        methodology = supabase.table('methodology_config').select('*').eq('id', methodology_id).limit(1).execute()
        
        if not methodology.data:
            return None
        
        result = methodology.data[0]
        result['pillars'] = []
        
        pillars = get_pillars_by_methodology(supabase, methodology_id)
        
        for pillar in pillars:
            pillar['criteria'] = []
            criteria = get_criteria_by_pillar(supabase, pillar['id'])
            
            for criterion in criteria:
                criterion['ranges'] = get_ranges_by_criterion(supabase, criterion['id'])
                pillar['criteria'].append(criterion)
            
            result['pillars'].append(pillar)
        
        return result
    except Exception as e:
        st.error(f"Erro ao buscar árvore de metodologia: {str(e)}")
        return None
