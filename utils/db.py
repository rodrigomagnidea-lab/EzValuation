import streamlit as st
from supabase import create_client, Client

# --- CONEXÃO ---
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

# --- FUNÇÕES QUE O WIZARD PRECISA ---

def get_active_methodology(supabase):
    """
    Busca a metodologia marcada como ativa (ou a última criada).
    Retorna None se não houver metodologias ou ocorrer erro.
    """
    try:
        # Tenta buscar uma que tenha um campo 'is_active', 
        # se não existir, pega a mais recente.
        res = supabase.table("methodology_config").select("*").order("created_at", desc=True).limit(1).execute()
        
        # Verifica se retornou dados
        if res.data and len(res.data) > 0:
            return res.data[0]
        else:
            # Tabela vazia ou sem resultados
            return None
    except Exception as e:
        # Qualquer erro (tabela não existe, campo faltando, etc.)
        st.warning(f"⚠️ Não foi possível carregar metodologia: {e}")
        return None

def get_full_methodology_tree(supabase, methodology_id):
    """
    Busca toda a estrutura (Pilares -> Critérios -> Faixas) de uma vez.
    Retorna lista vazia se houver erro ou nenhum dado.
    """
    try:
        # Esta função é um atalho para carregar tudo que o Wizard precisa
        pillars = supabase.table("pillar_config").select("*").eq("methodology_id", methodology_id).execute().data
        
        if not pillars:
            return []
        
        for p in pillars:
            p['criteria'] = supabase.table("criterion_config").select("*").eq("pillar_id", p['id']).execute().data
            for c in p['criteria']:
                c['thresholds'] = supabase.table("threshold_range").select("*").eq("criterion_id", c['id']).order("min_value").execute().data
        
        return pillars
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar estrutura da metodologia: {e}")
        return []

def create_analysis(supabase, data):
    """Salva uma nova análise de valuation."""
    return supabase.table("analysis_data").insert(data).execute()

def update_analysis(supabase, analysis_id, data):
    """Atualiza uma análise existente."""
    return supabase.table("analysis_data").update(data).eq("id", analysis_id).execute()

def get_user_analyses(supabase, user_id):
    """Busca histórico de análises de um usuário."""
    return supabase.table("analysis_data").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data

def get_analysis_by_id(supabase, analysis_id):
    """Busca uma análise específica."""
    res = supabase.table("analysis_data").select("*").eq("id", analysis_id).execute()
    return res.data[0] if res.data else None

# --- MANTENHA AS FUNÇÕES DE ADMIN QUE JÁ USAMOS ---
def get_market_indices(supabase):
    return supabase.table("market_indices").select("*").order("name").execute().data

def get_methodologies(supabase):
    return supabase.table("methodology_config").select("*").order("created_at").execute().data

def get_pillars_by_methodology(supabase, methodology_id):
    return supabase.table("pillar_config").select("*").eq("methodology_id", methodology_id).execute().data

def get_criteria_by_pillar(supabase, pillar_id):
    return supabase.table("criterion_config").select("*").eq("pillar_id", pillar_id).execute().data

def get_thresholds_by_criterion(supabase, criterion_id):
    return supabase.table("threshold_range").select("*").eq("criterion_id", criterion_id).execute().data
