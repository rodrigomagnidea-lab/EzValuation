import streamlit as st
from supabase import create_client, Client

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# --- FUNÇÕES DE ÍNDICES (Já existiam) ---
def get_market_indices(supabase):
    try:
        response = supabase.table("market_indices").select("*").order("name").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro DB: {e}")
        return []

# --- NOVAS FUNÇÕES: METODOLOGIA E ESTRUTURA ---

def get_methodologies(supabase):
    """Busca todas as metodologias cadastradas."""
    try:
        response = supabase.table("methodology_config").select("*").order("created_at").execute()
        return response.data
    except Exception as e:
        return []

def get_pillars_by_methodology(supabase, methodology_id):
    """Busca os pilares de uma metodologia específica."""
    try:
        response = supabase.table("pillar_config")\
            .select("*")\
            .eq("methodology_id", methodology_id)\
            .order("created_at")\
            .execute()
        return response.data
    except Exception as e:
        return []

def get_criteria_by_pillar(supabase, pillar_id):
    """Busca os critérios de um pilar."""
    try:
        response = supabase.table("criterion_config")\
            .select("*")\
            .eq("pillar_id", pillar_id)\
            .order("created_at")\
            .execute()
        return response.data
    except Exception as e:
        return []

def get_thresholds_by_criterion(supabase, criterion_id):
    """Busca as faixas de pontuação (verde/amarela/vermelha) de um critério."""
    try:
        response = supabase.table("threshold_range")\
            .select("*")\
            .eq("criterion_id", criterion_id)\
            .order("min_value")\
            .execute()
        return response.data
    except Exception as e:
        return []
