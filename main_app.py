"""
Music 10 - Painel Principal (Hub Central & Dashboard)
Aplicação web profissional para download, conversão, compressão e organização de músicas e metadados.
"""

import streamlit as st

# Configuração da página - DEVE ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Music 10 - Studio de Áudio & Mídia",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.ffmpeg_config import get_ffmpeg_status, setup_ffmpeg
from utils.theme_manager import apply_theme, render_theme_toggle_sidebar
from utils.state_manager import (
    init_session_state,
    get_active_track,
    set_active_track,
    clear_active_track,
    render_active_track_ribbon
)

# Inicializa estado e tema
init_session_state()
setup_ffmpeg()
apply_theme()

# Sidebar de navegação e preferências
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/sound-recording-copyright.png", width=64)
    st.markdown("## **Music 10**")
    st.caption("Studio Profissional de Mídia e Áudio")
    st.markdown("---")

    # Status do FFmpeg
    ffmpeg_info = get_ffmpeg_status()
    if ffmpeg_info["available"]:
        st.success("⚡ **FFmpeg:** Operacional & Integrado", icon="✅")
    else:
        st.warning("⚠️ **FFmpeg:** Não detectado automaticamente", icon="⚠️")

    # Alternador de Tema
    render_theme_toggle_sidebar()

# Cabeçalho Principal (Hero Banner)
st.html(
    """<div class="music10-header-card">
    <div class="music10-header-title">
        <span>🎵</span>
        <span>Music 10</span>
        <span class="music10-badge music10-badge-blue">Studio Pro</span>
    </div>
    <p class="music10-header-subtitle">
        Plataforma completa e integrada para <b>download de vídeos em MP3</b>, <b>compressão inteligente de áudio e imagens</b> e <b>organização profissional de tags ID3 e capas oficiais</b>.
    </p>
</div>"""
)

# Faixa Ativa Global (caso o usuário já tenha baixado ou carregado algo)
render_active_track_ribbon("home")

# Cards de Navegação Modular
st.markdown("### 🎛️ Módulos do Sistema")
col1, col2 = st.columns(2)

with col1:
    st.html(
        """<div class="music10-feature-card">
    <div>
        <div class="music10-feature-icon">🎵</div>
        <div class="music10-feature-title">YouTube para MP3 & Organizador de Tags ID3</div>
        <div class="music10-feature-desc">
            Extração de vídeos e músicas do YouTube / YouTube Music diretamente para MP3 com bitrate selecionável (320, 192 e 128 kbps), consulta oficial na <b>iTunes Search API</b>, edição de metadados e gravação de capas em alta resolução com Mutagen na mesma tela.
        </div>
    </div>
</div>"""
    )
    if st.button("Acessar Extrator & Tags ID3 ➔", key="btn_nav_yt", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🎵_YouTube_para_MP3.py")

with col2:
    st.html(
        """<div class="music10-feature-card">
    <div>
        <div class="music10-feature-icon">🗜️</div>
        <div class="music10-feature-title">Compressor de Mídia (Áudio & Imagens)</div>
        <div class="music10-feature-desc">
            Reduza o peso em MB de músicas (.mp3, .wav, .m4a, .ogg) ajustando o bitrate com comparativo em tempo real. Comprima também imagens em lote com redimensionamento proporcional e download em arquivo .ZIP.
        </div>
    </div>
</div>"""
    )
    if st.button("Acessar Compressores ➔", key="btn_nav_comp", use_container_width=True):
        st.switch_page("pages/2_🗜️_Compressor_Audio_Imagens.py")

st.markdown("---")

# Seção de Carregamento Rápido na Home
st.markdown("### ⚡ Carregamento Rápido de Áudio")
st.caption("Envie uma música agora para disponibilizá-la automaticamente em todos os módulos sem precisar reenviar:")

uploaded_quick = st.file_uploader(
    "Selecione um arquivo de áudio (.mp3, .wav, .m4a, .ogg)",
    type=["mp3", "wav", "m4a", "ogg"],
    key="home_quick_uploader"
)

if uploaded_quick is not None:
    audio_bytes = uploaded_quick.read()
    filename = uploaded_quick.name
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.audio(audio_bytes, format="audio/mp3")
    with col_b:
        if st.button("📥 Definir como Faixa Ativa", key="btn_set_active_home", type="primary", use_container_width=True):
            from utils.tag_manager import read_id3_tags_from_bytes
            existing_tags = read_id3_tags_from_bytes(audio_bytes) if filename.lower().endswith(".mp3") else {}
            
            set_active_track(
                audio_bytes=audio_bytes,
                filename=filename,
                title=existing_tags.get("title", filename),
                artist=existing_tags.get("artist", ""),
                album=existing_tags.get("album", ""),
                year=existing_tags.get("year", ""),
                genre=existing_tags.get("genre", ""),
                cover_bytes=existing_tags.get("cover_bytes"),
                cover_mime=existing_tags.get("cover_mime", "image/jpeg"),
                source="upload"
            )
            st.success(f"Faixa **{filename}** carregada no estado global com sucesso!")
            st.rerun()

# Histórico da Sessão
history = st.session_state.get("track_history", [])
if history:
    st.markdown("### 📜 Histórico de Faixas da Sessão")
    for idx, item in enumerate(history):
        st.html(
            f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 1rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem;">
    <div>
        <b>{item.get('title')}</b> {f"• {item.get('artist')}" if item.get('artist') else ''}
        <div style="font-size: 0.75rem; color: var(--text-muted);">Arquivo: {item.get('filename')} • {item.get('size_mb')} MB</div>
    </div>
    <span class="music10-badge">{item.get('source', 'processado')}</span>
</div>"""
        )

st.markdown("---")

# Guia Rápido de Direcionamento
st.html(
    """<div class="music10-card" style="border-left: 4px solid var(--accent-primary); padding: 1.6rem 1.8rem;">
    <h3 style="margin: 0 0 0.85rem 0; color: var(--text-main); font-size: 1.3rem; display: flex; align-items: center; gap: 0.6rem;">
        <span>🧭</span>
        <span>Guia Rápido de Uso do Music 10</span>
    </h3>
    <p style="color: var(--text-muted); font-size: 1.02rem; line-height: 1.6; margin-bottom: 1.25rem;">
        Conheça as principais ferramentas disponíveis para gerenciar, converter e organizar suas mídias:
    </p>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.1rem;">
        <div style="background: var(--bg-subtle); padding: 1.1rem 1.2rem; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-primary); font-size: 1.08rem; margin-bottom: 0.45rem;">🎵 1. Extrator & Tags ID3</div>
            <div style="font-size: 0.96rem; color: var(--text-main); opacity: 0.9; line-height: 1.55;">
                Cole o link do YouTube/YouTube Music, escolha a qualidade (320, 192 ou 128 kbps), consulte metadados e capas HD no iTunes e gere seu MP3 padronizado na mesma tela.
            </div>
        </div>
        <div style="background: var(--bg-subtle); padding: 1.1rem 1.2rem; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-primary); font-size: 1.08rem; margin-bottom: 0.45rem;">🎧 2. Compressor de Áudio</div>
            <div style="font-size: 0.96rem; color: var(--text-main); opacity: 0.9; line-height: 1.55;">
                Reduza o tamanho em MB de faixas (.mp3, .wav, .m4a, .ogg) ajustando o bitrate com comparativo antes/depois e estimativa de economia em tempo real.
            </div>
        </div>
        <div style="background: var(--bg-subtle); padding: 1.1rem 1.2rem; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-primary); font-size: 1.08rem; margin-bottom: 0.45rem;">🖼️ 3. Compressor de Imagens</div>
            <div style="font-size: 0.96rem; color: var(--text-main); opacity: 0.9; line-height: 1.55;">
                Otimize fotos e capas de álbuns em lote (.jpg, .png, .webp) com ajuste de qualidade, escala proporcional e download de tudo em arquivo .ZIP.
            </div>
        </div>
        <div style="background: var(--bg-subtle); padding: 1.1rem 1.2rem; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-primary); font-size: 1.08rem; margin-bottom: 0.45rem;">📂 4. Renomeador em Lote</div>
            <div style="font-size: 0.96rem; color: var(--text-main); opacity: 0.9; line-height: 1.55;">
                Padronize dezenas de arquivos em sequência numérica (ex: 001_img_nova.jpg) ou localize e delete/substitua trechos de texto com prévia instantânea.
            </div>
        </div>
    </div>
</div>"""
)
