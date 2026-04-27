import streamlit as st
import sys
import os

# Garante que o diretório raiz do projeto está no path para imports
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DASHBOARD_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

os.environ["MEDCASE_ROOT"] = PROJECT_ROOT


from core.database import load_artigos_csv, invalidate_cache

# ── Configuração da página ──────────────────────────────────────────
st.set_page_config(
    page_title="MedCase Explorer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
code, .stCode, pre { font-family: 'JetBrains Mono', monospace !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0D1117 !important;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #21262D;
}
            
[data-testid="stSidebarUserContent"] {
    display: flex;
    flex-direction: column;
    padding-bottom: 80px;
}

/* Footer */
.sidebar-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 18rem;
    padding: 12px 16px;
    font-size: 1.1rem;
    color: #515963;
    line-height: 1.6;
    text-align: center;
    background: #0D1117;
    border-top: 1px solid #21262D;
    z-index: 999;
}

/* Métricas nativas */
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.6rem !important;
    color: #4F8EF7 !important;
}
[data-testid="stMetricLabel"] { color: #8B949E !important; font-size: 0.75rem !important; }

/* Containers */
[data-testid="stExpander"] { border: 1px solid #21262D !important; border-radius: 8px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #161B22; border-radius: 8px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 6px 16px; color: #8B949E; }
.stTabs [aria-selected="true"] { background: #21262D !important; color: #E6EDF3 !important; }

/* Botões */
.stButton button {
    background: #21262D !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stButton button:hover { border-color: #4F8EF7 !important; }

/* Headers */
h1 { color: #E6EDF3 !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h2, h3 { color: #C9D1D9 !important; font-weight: 600 !important; }
hr { border-color: #21262D !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🩺 MedCase Explorer")
    st.markdown("---")

    if st.button("↺ Refresh Dados", width='stretch'):
        invalidate_cache()
        st.rerun()

    st.markdown("---")

    # Carregamento de dados automático
    try:
        df = load_artigos_csv()
        st.session_state["df"] = df
        
        total = len(df)
        com_relato = df["tem_relato"].sum() if not df.empty else 0
        st.markdown(f"""
        <div style="font-size:1.1rem; color:#8B949E; line-height:1.8">
        📄 <b style="color:#E6EDF3">{total:,}</b> artigos carregados<br>
        📋 <b style="color:#4F8EF7">{com_relato:,}</b> com relato de caso
        </div>
        """, unsafe_allow_html=True)
        st.success("✅ Dataset carregado")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        st.stop()

    st.markdown("---")

    # ── Navegação ──────────────────────────────────────────────────
    st.markdown("### 📊 Análises")

    paginas = {
        "🏠 Visão Geral": "visao_geral",
        "🔍 Sintomas": "sintomas",
        "🏷️ Palavras-chave": "palavras_chave",
        "📄 Explorar Artigos": "artigos",
    }

    # Hack para permitir navegação programática entre páginas
    if "next_page" in st.session_state:
        st.session_state["main_nav"] = st.session_state.pop("next_page")

    pagina_selecionada = st.radio(
        "Selecionar página",
        list(paginas.keys()),
        label_visibility="collapsed",
        key="main_nav"
    )

    st.markdown("---")
    st.markdown("""
    <div class="sidebar-footer">
    MedCase Explorer v1.0<br>
    Análise de Relatos de Caso — SciELO
    </div>
    """, unsafe_allow_html=True)

# ── Roteamento de páginas ──────────────────────────────────────────
pagina_key = paginas[pagina_selecionada]

if "df" not in st.session_state or st.session_state["df"].empty:
    st.warning("⚠️ Nenhum dado encontrado na coleção especificada.")
    st.stop()

df = st.session_state["df"]

if pagina_key == "visao_geral":
    from views import visao_geral
    visao_geral.render(df)

elif pagina_key == "sintomas":
    from views import sintomas
    sintomas.render(df)

elif pagina_key == "palavras_chave":
    from views import palavras_chave
    palavras_chave.render(df)

elif pagina_key == "artigos":
    from views import artigos
    artigos.render(df)

# elif pagina_key == "ner_comparacao":
#     from views import ner_comparacao
#     ner_comparacao.render(df)