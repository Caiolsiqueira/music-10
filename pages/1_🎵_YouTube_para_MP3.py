"""
Music 10 - Página 1: YouTube para MP3 & Organizador de Tags ID3 (Módulo Unificado)
Extração de áudio em MP3 com controle de bitrate e edição completa de metadados ID3 e capas na mesma página.
"""

import streamlit as st

st.set_page_config(
    page_title="YouTube para MP3 & Tags ID3 - Music 10",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.theme_manager import apply_theme, render_theme_toggle_sidebar
from utils.state_manager import (
    init_session_state,
    set_active_track,
    get_active_track,
    render_active_track_ribbon
)
from utils.youtube_extractor import (
    extract_video_info,
    download_audio_from_youtube,
    normalize_youtube_url
)
from utils.tag_manager import (
    search_itunes_metadata,
    download_artwork_bytes,
    read_id3_tags_from_bytes,
    write_id3_tags_to_mp3
)
from utils.ffmpeg_config import get_ffmpeg_status

init_session_state()
apply_theme()

# Inicialização das chaves do formulário no session_state
FORM_KEYS = [
    "unified_input_title",
    "unified_input_artist",
    "unified_input_album",
    "unified_input_year",
    "unified_input_genre",
    "unified_input_track",
    "unified_input_comments"
]

for key in FORM_KEYS:
    if key not in st.session_state:
        st.session_state[key] = ""

if "tag_form_cover_bytes" not in st.session_state:
    st.session_state["tag_form_cover_bytes"] = None

def update_form_state(
    title: str = "",
    artist: str = "",
    album: str = "",
    year: str = "",
    genre: str = "",
    track: str = "",
    comments: str = "",
    cover_bytes = None
):
    """Atualiza diretamente as variáveis conectadas aos widgets de input."""
    st.session_state["unified_input_title"] = title or ""
    st.session_state["unified_input_artist"] = artist or ""
    st.session_state["unified_input_album"] = album or ""
    st.session_state["unified_input_year"] = str(year) if year else ""
    st.session_state["unified_input_genre"] = genre or ""
    st.session_state["unified_input_track"] = str(track) if track else ""
    if comments:
        st.session_state["unified_input_comments"] = comments
    if cover_bytes is not None:
        st.session_state["tag_form_cover_bytes"] = cover_bytes

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/youtube-play.png", width=64)
    st.markdown("### **Music 10 Studio**")
    st.caption("Extrator YouTube, Conversor MP3 & Editor de Tags ID3 Integrados")
    st.markdown("---")
    
    ffmpeg_info = get_ffmpeg_status()
    if ffmpeg_info["available"]:
        st.success("⚡ **FFmpeg:** Operacional", icon="✅")
    else:
        st.error("⚠️ **FFmpeg:** Ausente", icon="⚠️")
        
    render_theme_toggle_sidebar()

# Cabeçalho
st.html(
    """<div class="music10-header-card">
    <div class="music10-header-title">
        <span>🎵</span>
        <span>YouTube para MP3 & Organizador de Tags ID3</span>
    </div>
    <p class="music10-header-subtitle">
        Extraia áudios em formato <b>MP3</b> do YouTube / YouTube Music com taxa de bits customizável e organize <b>metadados oficiais do iTunes e capas em alta resolução</b> tudo na mesma tela.
    </p>
</div>"""
)

render_active_track_ribbon("youtube_tagger")

# Seleção de modo de entrada: YouTube ou Upload Local
tab_yt, tab_upload = st.tabs(["📥 Extrair do YouTube / YouTube Music", "📁 Carregar MP3 do Computador"])

# ==========================================
# ABA 1: EXTRAÇÃO DO YOUTUBE
# ==========================================
with tab_yt:
    col_url, col_btn_prev = st.columns([4, 1])

    with col_url:
        yt_url = st.text_input(
            "Cole a URL do Vídeo ou Música (YouTube ou YouTube Music):",
            placeholder="https://www.youtube.com/watch?v=... ou https://music.youtube.com/watch?v=...",
            key="yt_url_input"
        )

    with col_btn_prev:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        check_preview = st.button("🔍 Carregar Prévia", key="btn_yt_preview", use_container_width=True)

    if "yt_preview_info" not in st.session_state:
        st.session_state["yt_preview_info"] = None

    if (check_preview or yt_url) and yt_url.strip():
        current_stored_url = st.session_state.get("yt_last_checked_url", "")
        if current_stored_url != yt_url.strip() or check_preview:
            with st.spinner("Buscando informações do vídeo..."):
                info = extract_video_info(yt_url.strip())
                if info.get("success"):
                    st.session_state["yt_preview_info"] = info
                    st.session_state["yt_last_checked_url"] = yt_url.strip()
                else:
                    st.session_state["yt_preview_info"] = None
                    st.error(info.get("error", "Erro ao carregar prévia do vídeo."))

    # Prévia do vídeo
    preview_data = st.session_state.get("yt_preview_info")
    if preview_data and preview_data.get("success"):
        st.html(
            f"""<div class="music10-preview-container">
    <img src="{preview_data.get('thumbnail')}" class="music10-preview-thumb" alt="Thumbnail" />
    <div class="music10-preview-details">
        <div class="music10-preview-title">{preview_data.get('title')}</div>
        <div class="music10-preview-meta">
            <b>Canal / Artista:</b> {preview_data.get('uploader')}<br/>
            <b>Duração:</b> ⏱️ {preview_data.get('duration_formatted')} min<br/>
            <b>Visualizações:</b> {preview_data.get('view_count'):,} visualizações
        </div>
    </div>
</div>"""
        )

    col_opt1, col_opt2 = st.columns([2, 2])

    with col_opt1:
        bitrate_label = st.selectbox(
            "Taxa de Bits (Bitrate) do Áudio Final:",
            options=[
                "Alta Fidelidade (320 kbps) - Máxima Qualidade",
                "Padrão / Equilibrado (192 kbps) - Recomendado",
                "Econômico / Mais Leve (128 kbps) - Menor Tamanho"
            ],
            index=1,
            key="select_bitrate_yt"
        )

        bitrate_mapping = {
            "Alta Fidelidade (320 kbps) - Máxima Qualidade": 320,
            "Padrão / Equilibrado (192 kbps) - Recomendado": 192,
            "Econômico / Mais Leve (128 kbps) - Menor Tamanho": 128
        }
        selected_bitrate = bitrate_mapping.get(bitrate_label, 192)

    with col_opt2:
        st.info(
            f"💡 **Perfil Selecionado:** `{selected_bitrate} kbps` em MP3 estéreo de alta fidelidade.",
            icon="ℹ️"
        )

    if st.button("🚀 Extrair e Converter Áudio para MP3", type="primary", use_container_width=True, key="btn_start_yt_extraction"):
        if not yt_url or not yt_url.strip():
            st.warning("Por favor, informe a URL do YouTube ou YouTube Music antes de continuar.")
        else:
            with st.status("Processando extração e conversão...", expanded=True) as status:
                st.write("📥 Conectando ao YouTube com bypass de verificação e baixando áudio...")
                result = download_audio_from_youtube(yt_url.strip(), bitrate_kbps=selected_bitrate)
                
                if result.get("success"):
                    st.write("🎧 Re-codificando para MP3 estéreo com FFmpeg...")
                    st.session_state["current_working_audio"] = result["audio_bytes"]
                    st.session_state["current_working_filename"] = result["filename"]
                    
                    # Atualiza os campos do formulário para o editor integrado
                    update_form_state(
                        title=result.get("title", ""),
                        artist=result.get("artist", ""),
                        album="",
                        year="",
                        genre="",
                        track="",
                        comments="Extraído com Music 10",
                        cover_bytes=result.get("cover_bytes")
                    )
                    
                    # Atualiza também a busca no iTunes
                    st.session_state["input_itunes_search_unified"] = f"{result.get('artist', '')} {result.get('title', '')}".strip()
                    
                    # Salva no estado global
                    set_active_track(
                        audio_bytes=result["audio_bytes"],
                        filename=result["filename"],
                        title=result.get("title", ""),
                        artist=result.get("artist", ""),
                        cover_bytes=result.get("cover_bytes"),
                        source="youtube",
                        duration_sec=result.get("duration", 0)
                    )
                    
                    status.update(label="🎉 Áudio extraído com sucesso! Agora você pode personalizar as tags abaixo.", state="complete", expanded=False)
                    st.success("Download e conversão concluídos com sucesso!")
                else:
                    status.update(label="❌ Erro na extração do áudio", state="error", expanded=True)
                    st.error(result.get("error", "Ocorreu um erro durante o download."))

# ==========================================
# ABA 2: UPLOAD LOCAL DE MP3
# ==========================================
with tab_upload:
    uploaded_local_mp3 = st.file_uploader(
        "Selecione um arquivo .MP3 do seu computador para organizar metadados e capa:",
        type=["mp3"],
        key="local_mp3_uploader_page1"
    )
    if uploaded_local_mp3 is not None:
        local_bytes = uploaded_local_mp3.read()
        local_name = uploaded_local_mp3.name
        
        st.session_state["current_working_audio"] = local_bytes
        st.session_state["current_working_filename"] = local_name
        
        # Lê tags existentes
        existing = read_id3_tags_from_bytes(local_bytes)
        title_found = existing.get("title") or local_name.replace(".mp3", "")
        artist_found = existing.get("artist", "")
        
        update_form_state(
            title=title_found,
            artist=artist_found,
            album=existing.get("album", ""),
            year=existing.get("year", ""),
            genre=existing.get("genre", ""),
            track=existing.get("track_num", ""),
            comments=existing.get("comments", "Organizado com Music 10"),
            cover_bytes=existing.get("cover_bytes")
        )
        
        st.session_state["input_itunes_search_unified"] = f"{artist_found} {title_found}".strip()
        
        set_active_track(
            audio_bytes=local_bytes,
            filename=local_name,
            title=title_found,
            artist=artist_found,
            source="upload"
        )
        st.success(f"Arquivo **{local_name}** carregado com sucesso!")

# =========================================================================
# SEÇÃO INTEGRADA: ORGANIZADOR DE TAGS ID3, ITUNES SEARCH API E CAPAS
# =========================================================================
active_audio = st.session_state.get("current_working_audio") or (get_active_track()["bytes"] if get_active_track() else None)
active_name = st.session_state.get("current_working_filename") or (get_active_track()["filename"] if get_active_track() else "musica.mp3")

if active_audio:
    st.markdown("---")
    st.markdown("### 🎧 Prévia do Áudio")
    
    col_prev_audio, col_dl_fast = st.columns([3, 1])
    with col_prev_audio:
        st.audio(active_audio, format="audio/mp3")
    with col_dl_fast:
        st.download_button(
            label=f"💾 Baixar MP3 Direto ({len(active_audio)/(1024*1024):.2f} MB)",
            data=active_audio,
            file_name=active_name,
            mime="audio/mp3",
            use_container_width=True,
            key="btn_dl_direct_mp3"
        )

    st.markdown("---")
    st.markdown("### 🏷️ Organizador de Tags ID3 & Capas Oficiais")
    st.caption("Consulte a base global do iTunes para preencher automaticamente artista, álbum, ano, gênero e capa em alta resolução.")

    # 1. BUSCA AUTOMÁTICA NO ITUNES
    if "input_itunes_search_unified" not in st.session_state:
        st.session_state["input_itunes_search_unified"] = f"{st.session_state.get('unified_input_artist', '')} {st.session_state.get('unified_input_title', '')}".strip() or active_name.replace(".mp3", "")

    col_s_in, col_s_btn = st.columns([4, 1])
    with col_s_in:
        itunes_query = st.text_input(
            "Buscar Música no iTunes:",
            key="input_itunes_search_unified"
        )
    with col_s_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_itunes_btn = st.button("🔎 Buscar no iTunes", use_container_width=True, key="btn_run_itunes_unified")

    if "itunes_search_results_unified" not in st.session_state:
        st.session_state["itunes_search_results_unified"] = []

    if search_itunes_btn and itunes_query:
        with st.spinner("Consultando biblioteca oficial do iTunes..."):
            res_itunes = search_itunes_metadata(itunes_query, limit=5)
            st.session_state["itunes_search_results_unified"] = res_itunes
            if not res_itunes:
                st.warning("Nenhum resultado encontrado no iTunes para esta busca.")

    search_results = st.session_state.get("itunes_search_results_unified", [])
    if search_results:
        st.markdown("#### Resultados Oficiais do iTunes:")
        for idx, item in enumerate(search_results):
            col_c1, col_c2, col_c3 = st.columns([1, 4, 2])
            with col_c1:
                if item.get("artwork_url"):
                    st.image(item["artwork_url"], width=75)
                else:
                    st.markdown("💿")
            with col_c2:
                st.markdown(f"**{item.get('title')}** • {item.get('artist')}")
                st.caption(f"Álbum: `{item.get('album')}` | Ano: `{item.get('year')}` | Gênero: `{item.get('genre')}`")
            with col_c3:
                if st.button(f"⚡ Aplicar #{idx+1}", key=f"btn_apply_itunes_unified_{idx}", use_container_width=True):
                    # Atualiza os dados de texto
                    update_form_state(
                        title=item.get("title", ""),
                        artist=item.get("artist", ""),
                        album=item.get("album", ""),
                        year=item.get("year", ""),
                        genre=item.get("genre", ""),
                        track=item.get("track_number", "")
                    )
                    
                    # Baixa a capa em alta resolução
                    art_url = item.get("artwork_ultra_url") or item.get("artwork_url")
                    if art_url:
                        with st.spinner("Baixando capa em alta resolução..."):
                            cover_bytes = download_artwork_bytes(art_url)
                            if cover_bytes:
                                st.session_state["tag_form_cover_bytes"] = cover_bytes
                    
                    st.toast("Metadados e capa do iTunes aplicados com sucesso!", icon="✨")
                    st.rerun()
            st.markdown("<hr style='margin: 0.35rem 0; opacity: 0.15;'/>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    
    # 2. FORMULÁRIO DE EDIÇÃO DE TAGS E CAPA
    col_form, col_cover = st.columns([2, 1])

    with col_form:
        edit_title = st.text_input("Título da Música (Title):", key="unified_input_title")
        edit_artist = st.text_input("Artista / Banda (Artist):", key="unified_input_artist")
        
        col_f_sub1, col_f_sub2 = st.columns(2)
        with col_f_sub1:
            edit_album = st.text_input("Álbum:", key="unified_input_album")
            edit_genre = st.text_input("Gênero Musical:", key="unified_input_genre")
        with col_f_sub2:
            edit_year = st.text_input("Ano:", key="unified_input_year")
            edit_track = st.text_input("Número da Faixa:", key="unified_input_track")
            
        edit_comments = st.text_area("Comentários:", key="unified_input_comments", height=68)

    with col_cover:
        st.markdown("#### 🖼️ Capa do Álbum")
        current_cover = st.session_state.get("tag_form_cover_bytes")
        if current_cover:
            st.image(current_cover, width=180, caption="Capa Ativa")
            if st.button("🗑️ Remover Capa", key="btn_remove_cover_unified"):
                st.session_state["tag_form_cover_bytes"] = None
                st.rerun()
        else:
            st.info("Nenhuma capa selecionada.")

        custom_cover_upload = st.file_uploader(
            "Enviar imagem de capa personalizada (.jpg, .png):",
            type=["jpg", "jpeg", "png", "webp"],
            key="custom_cover_uploader_unified"
        )
        if custom_cover_upload is not None:
            st.session_state["tag_form_cover_bytes"] = custom_cover_upload.read()
            st.rerun()

    # 3. GRAVAÇÃO FINAL DAS TAGS NO MP3
    if st.button("💾 Gravar Tags ID3 e Gerar MP3 Final Padronizado", type="primary", use_container_width=True, key="btn_save_final_tagged_mp3"):
        with st.spinner("Gravando tags ID3v2 e embutindo capa com Mutagen..."):
            save_result = write_id3_tags_to_mp3(
                audio_bytes=active_audio,
                title=edit_title,
                artist=edit_artist,
                album=edit_album,
                year=edit_year,
                genre=edit_genre,
                track_num=edit_track,
                comments=edit_comments,
                cover_bytes=st.session_state.get("tag_form_cover_bytes")
            )

            if save_result.get("success"):
                st.session_state["last_final_tagged_audio"] = save_result
                
                final_name = active_name
                if edit_artist and edit_title:
                    final_name = f"{edit_artist} - {edit_title}.mp3"
                elif edit_title:
                    final_name = f"{edit_title}.mp3"

                set_active_track(
                    audio_bytes=save_result["audio_bytes"],
                    filename=final_name,
                    title=edit_title,
                    artist=edit_artist,
                    album=edit_album,
                    year=edit_year,
                    genre=edit_genre,
                    cover_bytes=st.session_state.get("tag_form_cover_bytes"),
                    source="tagger"
                )
                st.success("Tags ID3 e capa embutidas com sucesso!")
            else:
                st.error(save_result.get("error", "Erro ao gravar tags no MP3."))

    # 4. EXIBIÇÃO DO MP3 FINAL PADRONIZADO
    tagged_final = st.session_state.get("last_final_tagged_audio")
    if tagged_final and tagged_final.get("success"):
        st.markdown("---")
        st.markdown("### 🎉 MP3 Final Completo (Pronto para Uso)")
        
        final_display_name = f"{edit_artist} - {edit_title}.mp3" if (edit_artist and edit_title) else active_name
        
        col_res_cov, col_res_info = st.columns([1, 3])
        with col_res_cov:
            if st.session_state.get("tag_form_cover_bytes"):
                st.image(st.session_state.get("tag_form_cover_bytes"), width=150)
            else:
                st.markdown("💿")
        with col_res_info:
            st.markdown(f"**Título:** {edit_title or 'Sem título'}")
            st.markdown(f"**Artista:** {edit_artist or 'Desconhecido'} | **Álbum:** {edit_album or 'Desconhecido'}")
            st.caption(f"Tamanho: `{tagged_final.get('size_mb')} MB` • Nome: `{final_display_name}`")
            st.audio(tagged_final["audio_bytes"], format="audio/mp3")

        st.download_button(
            label=f"💾 Baixar MP3 Final com Tags & Capa ({tagged_final.get('size_mb')} MB)",
            data=tagged_final["audio_bytes"],
            file_name=final_display_name,
            mime="audio/mp3",
            type="primary",
            use_container_width=True,
            key="btn_dl_ultimate_tagged_mp3"
        )
else:
    st.info("👆 Extraia uma música do YouTube acima ou carregue um arquivo MP3 para começar a organizar as tags.")
