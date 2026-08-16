"""
Music 10 - Página 2: Compressor & Organizador de Mídia
Compressão de áudios e imagens, e organizador/renomeador de arquivos em lote com download em ZIP.
"""

import streamlit as st

st.set_page_config(
    page_title="Compressor & Organizador - Music 10",
    page_icon="🗜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.theme_manager import apply_theme, render_theme_toggle_sidebar
from utils.state_manager import (
    init_session_state,
    get_active_track,
    set_active_track,
    render_active_track_ribbon
)
from utils.audio_processor import compress_audio, get_audio_info_from_bytes, estimate_compressed_size_mb
from utils.image_processor import compress_single_image, create_zip_from_images
from utils.file_renamer import rename_sequential, rename_find_and_replace, create_zip_from_renamed_files
from utils.ffmpeg_config import get_ffmpeg_status

init_session_state()
apply_theme()

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/compress.png", width=64)
    st.markdown("### **Compressor & Mídia**")
    st.caption("Compressão de músicas, imagens e renomeação em lote de arquivos")
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
        <span>🗜️</span>
        <span>Compressor de Mídia & Organizador de Arquivos</span>
    </div>
    <p class="music10-header-subtitle">
        Otimize suas músicas para economizar espaço, converta imagens e <b>renomeie e padronize arquivos em lote</b> com exportação em ZIP.
    </p>
</div>"""
)

render_active_track_ribbon("compressor")

tab_audio, tab_images, tab_renamer = st.tabs([
    "🎧 Compressor de Áudio",
    "🖼️ Compressor de Imagens",
    "📂 Renomeador & Organizador de Arquivos"
])

# ==========================================
# ABA 1: COMPRESSOR DE ÁUDIO
# ==========================================
with tab_audio:
    st.markdown("### 🎚️ Otimização e Redução de Tamanho de Áudio")
    st.caption("Suporta formatos `.mp3`, `.wav`, `.m4a` e `.ogg` com re-codificação de bitrate em tempo real.")

    active_track = get_active_track()
    audio_source_option = "Novo Upload"

    if active_track and active_track.get("bytes"):
        audio_source_option = st.radio(
            "Fonte do Áudio:",
            options=["Usar Faixa Ativa na Memória", "Fazer Upload de Novo Arquivo"],
            horizontal=True,
            key="radio_audio_source"
        )

    target_audio_bytes = None
    target_filename = ""

    if audio_source_option == "Usar Faixa Ativa na Memória" and active_track:
        target_audio_bytes = active_track.get("bytes")
        target_filename = active_track.get("filename", "faixa_ativa.mp3")
        st.info(f"🎵 Utilizando faixa ativa: **{target_filename}** ({active_track.get('size_mb', 0)} MB)")
    else:
        uploaded_audio = st.file_uploader(
            "Selecione um arquivo de áudio:",
            type=["mp3", "wav", "m4a", "ogg"],
            key="compressor_audio_uploader"
        )
        if uploaded_audio:
            target_audio_bytes = uploaded_audio.read()
            target_filename = uploaded_audio.name

    if target_audio_bytes and target_filename:
        st.markdown("---")
        
        # Análise do áudio original
        info = get_audio_info_from_bytes(target_audio_bytes, ext=target_filename.split(".")[-1])
        orig_duration = info.get("duration_sec", 0.0) if info.get("success") else 0.0
        orig_size_mb = len(target_audio_bytes) / (1024 * 1024)

        col_cfg1, col_cfg2 = st.columns([2, 1])
        
        with col_cfg1:
            bitrate_slider = st.select_slider(
                "Selecione a Taxa de Bits Alvo (Bitrate):",
                options=[64, 96, 128, 160, 192, 224, 256, 320],
                value=128,
                format_func=lambda x: f"{x} kbps" + (" (Mais Leve)" if x == 64 else (" (Equilibrado)" if x == 128 else (" (Máxima Qualidade)" if x == 320 else ""))),
                key="slider_audio_bitrate"
            )

        with col_cfg2:
            st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
            to_mono = st.checkbox("Converter para Mono (Redução Adicional)", value=False, help="Ideal para podcasts, aulas ou gravações de voz.")

        # Estimativa de tamanho
        est_size = estimate_compressed_size_mb(orig_duration, bitrate_slider) if orig_duration > 0 else 0.0
        est_saved = max(0.0, orig_size_mb - est_size)
        est_percent = (est_saved / orig_size_mb * 100) if orig_size_mb > 0 else 0.0

        st.html(
            f"""<div class="music10-compare-grid">
    <div class="music10-stat-box">
        <div class="music10-stat-label">Tamanho Original</div>
        <div class="music10-stat-value">{orig_size_mb:.2f} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Estimativa Final ({bitrate_slider} kbps)</div>
        <div class="music10-stat-value music10-stat-saved">{est_size:.2f} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Economia Estimada</div>
        <div class="music10-stat-value music10-stat-saved">~{est_percent:.0f}%</div>
    </div>
</div>"""
        )

        if st.button("🗜️ Processar e Comprimir Áudio Agora", type="primary", use_container_width=True, key="btn_run_audio_compression"):
            with st.spinner("Re-codificando áudio com FFmpeg..."):
                comp_result = compress_audio(
                    file_bytes=target_audio_bytes,
                    original_filename=target_filename,
                    target_bitrate_kbps=bitrate_slider,
                    to_mono=to_mono
                )

                if comp_result.get("success"):
                    st.session_state["last_compressed_audio"] = comp_result
                    
                    # Atualiza o estado global
                    set_active_track(
                        audio_bytes=comp_result["audio_bytes"],
                        filename=comp_result["filename"],
                        title=comp_result["filename"],
                        source="compressor",
                        duration_sec=comp_result.get("duration_sec", 0.0)
                    )
                    st.success("Compressão de áudio finalizada com sucesso!")
                else:
                    st.error(comp_result.get("error", "Erro ao comprimir áudio."))

        # Exibição do Resultado da Compressão
        comp_data = st.session_state.get("last_compressed_audio")
        if comp_data and comp_data.get("success"):
            st.markdown("---")
            st.markdown("#### 🎉 Áudio Comprimido com Sucesso")
            
            st.html(
                f"""<div class="music10-compare-grid">
    <div class="music10-stat-box">
        <div class="music10-stat-label">Antes</div>
        <div class="music10-stat-value">{comp_data.get('original_size_mb')} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Depois</div>
        <div class="music10-stat-value music10-stat-saved">{comp_data.get('new_size_mb')} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Espaço Economizado</div>
        <div class="music10-stat-value music10-stat-saved">{comp_data.get('saved_percent')}% (-{comp_data.get('saved_mb')} MB)</div>
    </div>
</div>"""
            )

            st.audio(comp_data["audio_bytes"], format="audio/mp3")

            col_down, col_tag = st.columns([1, 1])
            with col_down:
                st.download_button(
                    label=f"💾 Baixar MP3 Otimizado ({comp_data.get('new_size_mb')} MB)",
                    data=comp_data["audio_bytes"],
                    file_name=comp_data.get("filename", "audio_comprimido.mp3"),
                    mime="audio/mp3",
                    type="primary",
                    use_container_width=True,
                    key="btn_dl_compressed_mp3"
                )
            with col_tag:
                if st.button("🏷️ Enviar para Editor de Tags ID3 ➔", use_container_width=True, key="btn_send_tagger_from_comp"):
                    st.switch_page("pages/1_🎵_YouTube_para_MP3.py")

# ==========================================
# ABA 2: COMPRESSOR DE IMAGENS
# ==========================================
with tab_images:
    st.markdown("### 🖼️ Otimização e Compressão de Imagens")
    st.caption("Comprima capas de álbuns, artes ou fotos nos formatos `.jpg`, `.png` e `.webp` com download individual ou pacote `.zip`.")

    uploaded_images = st.file_uploader(
        "Selecione uma ou mais imagens:",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="compressor_images_uploader"
    )

    if uploaded_images:
        col_img_opt1, col_img_opt2, col_img_opt3 = st.columns(3)

        with col_img_opt1:
            quality_slider = st.slider("Qualidade de Compressão (1 a 100):", min_value=10, max_value=100, value=80, step=5, key="slider_img_quality")

        with col_img_opt2:
            scale_slider = st.slider("Escala / Redimensionamento (%):", min_value=20, max_value=100, value=100, step=10, key="slider_img_scale")

        with col_img_opt3:
            format_choice = st.selectbox(
                "Formato de Saída:",
                options=["Manter Formato Original (Auto)", "JPEG (.jpg)", "WEBP (.webp)", "PNG (.png)"],
                index=0,
                key="select_img_format"
            )
            fmt_map = {
                "Manter Formato Original (Auto)": "AUTO",
                "JPEG (.jpg)": "JPEG",
                "WEBP (.webp)": "WEBP",
                "PNG (.png)": "PNG"
            }
            chosen_format = fmt_map.get(format_choice, "AUTO")

        if st.button("⚡ Comprimir Todas as Imagens", type="primary", use_container_width=True, key="btn_run_img_compression"):
            with st.spinner("Processando e otimizando imagens com Pillow..."):
                results = []
                total_orig_kb = 0.0
                total_new_kb = 0.0

                for img_file in uploaded_images:
                    img_bytes = img_file.read()
                    res = compress_single_image(
                        image_bytes=img_bytes,
                        original_filename=img_file.name,
                        quality=quality_slider,
                        scale_percent=scale_slider,
                        output_format=chosen_format
                    )
                    results.append(res)
                    if res.get("success"):
                        total_orig_kb += res.get("original_size_kb", 0)
                        total_new_kb += res.get("new_size_kb", 0)

                st.session_state["image_compression_results"] = {
                    "items": results,
                    "total_orig_kb": total_orig_kb,
                    "total_new_kb": total_new_kb,
                    "total_saved_kb": max(0.0, total_orig_kb - total_new_kb),
                    "total_saved_pct": (max(0.0, total_orig_kb - total_new_kb) / total_orig_kb * 100) if total_orig_kb > 0 else 0
                }

        # Exibição dos Resultados de Imagens
        img_results_data = st.session_state.get("image_compression_results")
        if img_results_data and img_results_data.get("items"):
            st.markdown("---")
            st.markdown("### 📊 Resultado da Otimização de Imagens")
            
            # Resumo Geral
            st.html(
                f"""<div class="music10-compare-grid">
    <div class="music10-stat-box">
        <div class="music10-stat-label">Total Original</div>
        <div class="music10-stat-value">{img_results_data['total_orig_kb'] / 1024:.2f} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Total Otimizado</div>
        <div class="music10-stat-value music10-stat-saved">{img_results_data['total_new_kb'] / 1024:.2f} MB</div>
    </div>
    <div class="music10-stat-box">
        <div class="music10-stat-label">Economia Total</div>
        <div class="music10-stat-value music10-stat-saved">{img_results_data['total_saved_pct']:.1f}%</div>
    </div>
</div>"""
            )

            # Botão de download em ZIP se houver múltiplos arquivos
            if len(img_results_data["items"]) > 1:
                zip_bytes = create_zip_from_images(img_results_data["items"])
                st.download_button(
                    label="📦 Baixar Todas as Imagens em Pacote .ZIP",
                    data=zip_bytes,
                    file_name="imagens_otimizadas_music10.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="btn_dl_all_images_zip"
                )
                st.markdown("<br/>", unsafe_allow_html=True)

            # Lista individual de imagens
            for idx, item in enumerate(img_results_data["items"]):
                if item.get("success"):
                    col_prev, col_info, col_btn = st.columns([1, 2, 1])
                    with col_prev:
                        st.image(item["image_bytes"], width=120)
                    with col_info:
                        st.markdown(f"**{item.get('filename')}**")
                        st.caption(
                            f"Dimensões: `{item.get('original_dimensions')}` ➔ `{item.get('new_dimensions')}`<br/>"
                            f"Peso: `{item.get('original_size_kb')} KB` ➔ **`{item.get('new_size_kb')} KB`** "
                            f"<span class='music10-badge'>-{item.get('saved_percent')}%</span>",
                            unsafe_allow_html=True
                        )
                    with col_btn:
                        st.download_button(
                            label=f"💾 Baixar ({item.get('new_size_kb')} KB)",
                            data=item["image_bytes"],
                            file_name=item.get("filename"),
                            mime=f"image/{item.get('format', 'jpeg').lower()}",
                            use_container_width=True,
                            key=f"btn_dl_single_img_{idx}"
                        )
                    st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'/>", unsafe_allow_html=True)

# =========================================================================
# ABA 3: ORGANIZADOR E RENOMEADOR DE ARQUIVOS EM LOTE
# =========================================================================
with tab_renamer:
    st.markdown("### 📂 Organizador e Renomeador de Arquivos em Lote")
    st.caption("Carregue múltiplos arquivos (imagens, músicas, documentos) para renomear em sequência ou remover/substituir trechos de texto.")

    uploaded_batch_files = st.file_uploader(
        "Selecione os arquivos para renomear e organizar:",
        accept_multiple_files=True,
        key="batch_renamer_uploader"
    )

    if uploaded_batch_files:
        files_data = [(f.name, f.read()) for f in uploaded_batch_files]
        st.info(f"📁 **{len(files_data)}** arquivo(s) carregado(s) com sucesso.")

        # Seleção do Modo de Renomeação
        renaming_mode = st.radio(
            "Selecione a Operação de Renomeação:",
            options=[
                "🔢 Modo 1: Padronização Sequencial (ex: 001_img_nova, 002_img_nova...)",
                "✂️ Modo 2: Localizar e Deletar / Substituir Texto (ex: remover '_nova' dos nomes)"
            ],
            key="radio_renaming_mode"
        )

        renamed_results = []

        # CONFIGURAÇÃO DO MODO 1: SEQUENCIAL
        if "Modo 1" in renaming_mode:
            st.markdown("#### ⚙️ Configurações da Sequência Numérica")
            col_seq1, col_seq2, col_seq3 = st.columns(3)

            with col_seq1:
                base_name_input = st.text_input(
                    "Nome Base do Arquivo:",
                    value="img_nova",
                    help="Texto que acompanhará o número (ex: 'img_nova' gerará '001_img_nova.jpg')",
                    key="input_seq_base_name"
                )

            with col_seq2:
                digit_choice = st.selectbox(
                    "Formato dos Dígitos:",
                    options=["3 dígitos (001, 002...)", "2 dígitos (01, 02...)", "1 dígito (1, 2...)"],
                    index=0,
                    key="select_seq_digits"
                )
                digit_map = {
                    "3 dígitos (001, 002...)": 3,
                    "2 dígitos (01, 02...)": 2,
                    "1 dígito (1, 2...)": 1
                }
                digits_val = digit_map.get(digit_choice, 3)

            with col_seq3:
                pos_choice = st.selectbox(
                    "Posição do Número:",
                    options=["Prefixo (001_nome.ext)", "Sufixo (nome_001.ext)"],
                    index=0,
                    key="select_seq_position"
                )
                pos_val = "prefix" if "Prefixo" in pos_choice else "suffix"

            col_sep, col_start = st.columns(2)
            with col_sep:
                sep_choice = st.selectbox(
                    "Separador:",
                    options=["_ (Underline)", "- (Hífen)", "Espaço ( )", "Nenhum"],
                    index=0,
                    key="select_seq_separator"
                )
                sep_map = {
                    "_ (Underline)": "_",
                    "- (Hífen)": "-",
                    "Espaço ( )": " ",
                    "Nenhum": ""
                }
                sep_val = sep_map.get(sep_choice, "_")

            with col_start:
                start_num = st.number_input(
                    "Iniciar contagem em:",
                    min_value=1,
                    value=1,
                    step=1,
                    key="input_seq_start_num"
                )

            # Gera pré-visualização em tempo real
            renamed_results = rename_sequential(
                files=files_data,
                base_name=base_name_input,
                digits=digits_val,
                position=pos_val,
                separator=sep_val,
                start_index=int(start_num)
            )

        # CONFIGURAÇÃO DO MODO 2: FIND & REPLACE / REMOÇÃO
        else:
            st.markdown("#### ⚙️ Localizar e Remover / Substituir Texto")
            col_rep1, col_rep2 = st.columns(2)

            with col_rep1:
                text_to_delete = st.text_input(
                    "Texto para Localizar / Deletar:",
                    value="_nova",
                    placeholder="Ex: _nova, [Audio], (Clipe Oficial)...",
                    help="Este trecho será removido do nome de todos os arquivos carregados.",
                    key="input_rep_search"
                )

            with col_rep2:
                replace_with = st.text_input(
                    "Substituir por (opcional):",
                    value="",
                    placeholder="Deixe em branco para apenas deletar o texto",
                    help="Deixe vazio se quiser apenas excluir o texto localizado.",
                    key="input_rep_replace"
                )

            col_opt_rep1, col_opt_rep2 = st.columns(2)
            with col_opt_rep1:
                case_sensitive = st.checkbox("Diferenciar Maiúsculas / Minúsculas (Case-sensitive)", value=False, key="check_rep_case")
                clean_extra_spaces = st.checkbox("Limpar espaços e separadores duplos", value=True, key="check_rep_spaces")

            with col_opt_rep2:
                case_mode_choice = st.selectbox(
                    "Formatação de Caixa do Nome:",
                    options=["Manter Original", "minúsculas (lowercase)", "MAIÚSCULAS (UPPERCASE)", "Primeira Letra Maiúscula (Title Case)"],
                    index=0,
                    key="select_rep_case_mode"
                )
                case_map = {
                    "Manter Original": "none",
                    "minúsculas (lowercase)": "lower",
                    "MAIÚSCULAS (UPPERCASE)": "upper",
                    "Primeira Letra Maiúscula (Title Case)": "title"
                }
                case_mode_val = case_map.get(case_mode_choice, "none")

            # Gera pré-visualização em tempo real
            renamed_results = rename_find_and_replace(
                files=files_data,
                search_text=text_to_delete,
                replace_text=replace_with,
                case_sensitive=case_sensitive,
                clean_spaces=clean_extra_spaces,
                case_mode=case_mode_val
            )

        # TABELA DE PRÉVIA EM TEMPO REAL
        if renamed_results:
            st.markdown("---")
            st.markdown("### 📋 Prévia da Renomeação (Antes ➔ Depois)")

            preview_table_data = []
            for idx, res in enumerate(renamed_results, start=1):
                preview_table_data.append({
                    "#": idx,
                    "Nome Original": res["original_name"],
                    "➔ Novo Nome Gerado": res["new_name"],
                    "Tamanho": f"{res['size_kb']} KB"
                })

            st.dataframe(preview_table_data, use_container_width=True, hide_index=True)

            # BOTÃO DE DOWNLOAD DO PACOTE ZIP
            st.markdown("<br/>", unsafe_allow_html=True)
            zip_package_bytes = create_zip_from_renamed_files(renamed_results)

            st.download_button(
                label=f"📦 Baixar Todos os {len(renamed_results)} Arquivos Renomeados (.ZIP)",
                data=zip_package_bytes,
                file_name="arquivos_organizados_music10.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
                key="btn_download_renamed_zip"
            )
