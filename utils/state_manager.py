"""
Music 10 - Gerenciador de Estado Global (st.session_state)
Centraliza o compartilhamento de arquivos de áudio, metadados e capas
entre todos os módulos do Streamlit.
"""

from typing import Optional, Dict, Any
import streamlit as st

DEFAULT_TRACK_STATE = {
    "bytes": None,
    "filename": "",
    "title": "",
    "artist": "",
    "album": "",
    "year": "",
    "genre": "",
    "track_num": "",
    "comments": "",
    "cover_bytes": None,
    "cover_mime": "image/jpeg",
    "source": "",
    "size_mb": 0.0,
    "duration_sec": 0.0,
}

def init_session_state():
    """Inicializa todas as chaves globais do session_state caso não existam."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    if "active_track" not in st.session_state:
        st.session_state["active_track"] = None

    if "track_history" not in st.session_state:
        st.session_state["track_history"] = []

    if "pending_toast" not in st.session_state:
        st.session_state["pending_toast"] = None

def set_active_track(
    audio_bytes: bytes,
    filename: str,
    title: str = "",
    artist: str = "",
    album: str = "",
    year: str = "",
    genre: str = "",
    track_num: str = "",
    comments: str = "",
    cover_bytes: Optional[bytes] = None,
    cover_mime: str = "image/jpeg",
    source: str = "upload",
    duration_sec: float = 0.0
):
    """
    Define a faixa ativa global que poderá ser consumida pelo compressor
    ou editor de tags em qualquer página.
    """
    init_session_state()
    size_mb = len(audio_bytes) / (1024 * 1024) if audio_bytes else 0.0

    track_data = {
        "bytes": audio_bytes,
        "filename": filename or "track.mp3",
        "title": title,
        "artist": artist,
        "album": album,
        "year": year,
        "genre": genre,
        "track_num": track_num,
        "comments": comments,
        "cover_bytes": cover_bytes,
        "cover_mime": cover_mime,
        "source": source,
        "size_mb": round(size_mb, 2),
        "duration_sec": round(duration_sec, 1)
    }

    st.session_state["active_track"] = track_data

    # Adiciona ao histórico (mantém até 10 itens)
    history = st.session_state.get("track_history", [])
    history.insert(0, {
        "filename": filename,
        "title": title or filename,
        "artist": artist,
        "size_mb": round(size_mb, 2),
        "source": source
    })
    st.session_state["track_history"] = history[:10]

def get_active_track() -> Optional[Dict[str, Any]]:
    """Retorna os dados da faixa ativa ou None se não houver."""
    init_session_state()
    return st.session_state.get("active_track")

def clear_active_track():
    """Limpa a faixa ativa do estado."""
    init_session_state()
    st.session_state["active_track"] = None

def render_active_track_ribbon(current_page: str = ""):
    """
    Renderiza um componente visual informativo na página indicando a faixa
    atualmente carregada no estado global com botões de ação rápida.
    """
    track = get_active_track()
    if not track or not track.get("bytes"):
        return

    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        title_disp = track.get("title") or track.get("filename")
        artist_disp = f" • {track.get('artist')}" if track.get("artist") else ""
        source_label = {
            "youtube": "Extraído do YouTube",
            "compressor": "Otimizado pelo Compressor",
            "tagger": "Processado no Editor de Tags",
            "upload": "Carregado via Upload"
        }.get(track.get("source", ""), "Faixa em Memória")

        html_ribbon = f"""<div class="music10-session-ribbon">
    <div class="music10-session-info">
        <span style="font-size: 1.5rem;">🎵</span>
        <div>
            <div class="music10-session-title">{title_disp}{artist_disp}</div>
            <div class="music10-session-meta">
                <span class="music10-badge">{source_label}</span>
                &nbsp; Tamanho: <b>{track.get('size_mb', 0)} MB</b>
            </div>
        </div>
    </div>
</div>"""
        if hasattr(st, "html"):
            st.html(html_ribbon)
        else:
            st.markdown(html_ribbon, unsafe_allow_html=True)

    with col2:
        if current_page != "youtube_tagger":
            if st.button("🏷️ Abrir no Extrator & Tags", key=f"ribbon_yt_tag_{current_page}", use_container_width=True):
                st.switch_page("pages/1_🎵_YouTube_para_MP3.py")
        elif current_page != "compressor":
            if st.button("🗜️ Abrir no Compressor", key=f"ribbon_comp_{current_page}", use_container_width=True):
                st.switch_page("pages/2_🗜️_Compressor_Audio_Imagens.py")

    with col3:
        if st.button("🗑️ Liberar Faixa", key=f"ribbon_clear_{current_page}", use_container_width=True):
            clear_active_track()
            st.rerun()
