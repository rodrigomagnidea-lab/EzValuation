import streamlit as st
from supabase import create_client, Client

# --- CONEXÃO ---
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        # Padrão minúsculo que você confirmou que funciona
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro nos segredos: {e}")
        st.stop()

# --- FUNÇÕES ---
def get_market_indices(supabase):
    try:
        return supabase.table("market_indices").select("*").order("name").execute().data
    except:
        return []

def get_methodologies(supabase):
    try:
        return supabase.table("methodology_config").select("*").order("created_at").execute().data
    except:
        return []

def get_pillars_by_methodology(supabase, methodology_id):
    try:
        return supabase.table("pillar_config").select("*").eq("methodology_id", methodology_id).order("created_at").execute().data
    except:
        return []

def get_criteria_by_pillar(supabase, pillar_id):
    try:
        return supabase.table("criterion_config").select("*").eq("pillar_id", pillar_id).order("created_at").execute().data
    except:
        return []

def get_thresholds_by_criterion(supabase, criterion_id):
    try:
        return supabase.table("threshold_range").select("*").eq("criterion_id", criterion_id).order("min_value").execute().data
    except:
        return []
