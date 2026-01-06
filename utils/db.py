import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXÃO COM SUPABASE (BLINDADA) ---
@st.cache_resource
def get_supabase_client() -> Client:
    # Tenta pegar as chaves do jeito padrão (SUPABASE_URL)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except KeyError:
        # Se falhar, tenta pegar do jeito aninhado ([supabase] url=...)
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except KeyError:
            st.error("❌ Erro Crítico: Chaves do Supabase não encontradas nos Secrets.")
            st.stop()
    return create_client(url, key)

# --- 2. FUNÇÕES DE ÍNDICES ---
def get_market_indices(supabase):
    try:
        response = supabase.table("market_indices").select("*").order("name").execute()
        return response.data
    except Exception as e:
        return []

# --- 3. FUNÇÕES DE METODOLOGIA (O que estava faltando!) ---
def get_methodologies(supabase):
    try:
        response = supabase.table("methodology_config").select("*").order("created_at").execute()
        return response.data
    except Exception as e:
        return []

def get_pillars_by_methodology(supabase, methodology_id):
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
    try:
        response = supabase.table("threshold_range")\
            .select("*")\
            .eq("criterion_id", criterion_id)\
            .order("min_value")\
            .execute()
        return response.data
    except Exception as e:
        return []
