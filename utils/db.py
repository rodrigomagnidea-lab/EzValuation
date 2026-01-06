import streamlit as st
from supabase import create_client, Client

# --- CONEXÃO COM SUPABASE (Usando o padrão minúsculo que funcionou) ---
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        # Usando o caminho minúsculo conforme sua experiência anterior
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao ler segredos: {e}")
        st.stop()

# --- FUNÇÕES DE ÍNDICES ---
def get_market_indices(supabase):
    try:
        response = supabase.table("market_indices").select("*").order("name").execute()
        return response.data
    except:
        return []

# --- FUNÇÕES PARA O NOVO LAYOUT (O que o wizard está procurando) ---
def get_methodologies(supabase):
    try:
        response = supabase.table("methodology_config").select("*").order("created_at").execute()
        return response.data
    except:
        return []

def get_pillars_by_methodology(supabase, methodology_id):
    try:
        response = supabase.table("pillar_config").select("*").eq("methodology_id", methodology_id).order("created_at").execute()
        return response.data
    except:
        return []

def get_criteria_by_pillar(supabase, pillar_id):
    try:
        response = supabase.table("criterion_config").select("*").eq("pillar_id", pillar_id).order("created_at").execute()
        return response.data
    except:
        return []

def get_thresholds_by_criterion(supabase, criterion_id):
    try:
        response = supabase.table("threshold_range").select("*").eq("criterion_id", criterion_id).order("min_value").execute()
        return response.data
    except:
        return []
