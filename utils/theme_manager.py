"""
Music 10 - Gerenciador de Estilos (Modo Escuro Studio Exclusivo)
Aplica o CSS customizado do modo escuro via st.markdown sem vazamento de código ou scripts desnecessários.
"""

import os
import textwrap
import streamlit as st

def get_css_content() -> str:
    """Lê o arquivo CSS customizado da pasta assets."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def apply_theme():
    """Aplica o CSS customizado do modo escuro de forma 100% limpa."""
    extra_css = get_css_content()
    
    dark_css = textwrap.dedent(f"""
        <style>
            .stApp {{
                background-color: #0e1117 !important;
                color: #f8fafc !important;
            }}
            [data-testid="stSidebar"] {{
                background-color: #161a23 !important;
                border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            }}
            header[data-testid="stHeader"] {{
                background: rgba(14, 17, 23, 0.9) !important;
            }}
            .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input, .stTextArea textarea {{
                background-color: #1e2330 !important;
                color: #f8fafc !important;
                border-color: rgba(255, 255, 255, 0.12) !important;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                background-color: #181c24;
                border-radius: 8px;
                padding: 4px;
            }}
            .stTabs [data-baseweb="tab"] {{
                color: #94a3b8;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: #232834 !important;
                color: #1db954 !important;
                font-weight: 700;
                border-radius: 6px;
            }}
            {extra_css}
        </style>
    """).strip()

    st.markdown(dark_css, unsafe_allow_html=True)

def render_theme_toggle_sidebar():
    """Renderiza informações do sistema e versão na barra lateral."""
    st.sidebar.markdown("---")
    sidebar_info = textwrap.dedent("""
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem; text-align: center;">
            <b>Music 10 Pro</b> • v1.0.0<br/>
            <span style="color: #1db954;">● Modo Escuro Studio</span><br/>
            Engine: Python + FFmpeg + Mutagen
        </div>
    """).strip()
    st.sidebar.markdown(sidebar_info, unsafe_allow_html=True)
