"""
Music 10 - Módulo Extrator de YouTube para MP3 (yt-dlp + FFmpeg)
Permite obter informações rápidas de vídeos e extrair áudio com bitrate configurável,
com suporte a bypass de bot do YouTube, URLs do YouTube Music e fallback multi-estratégia.
"""

import os
import re
import tempfile
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse
from .ffmpeg_config import get_ffmpeg_path

def get_cookie_file_path() -> Optional[str]:
    """
    Verifica se existem cookies do YouTube configurados no Streamlit Cloud (st.secrets)
    ou em um arquivo cookies.txt no diretório do projeto.
    """
    local_cookies = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
    if os.path.exists(local_cookies) and os.path.getsize(local_cookies) > 10:
        return local_cookies

    test_cookies = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_cookies.txt")
    if os.path.exists(test_cookies) and os.path.getsize(test_cookies) > 10:
        return test_cookies

    try:
        import streamlit as st
        if hasattr(st, "secrets") and "YOUTUBE_COOKIES" in st.secrets:
            cookie_content = st.secrets["YOUTUBE_COOKIES"]
            if cookie_content and len(cookie_content.strip()) > 10:
                temp_cookie = os.path.join(tempfile.gettempdir(), "yt_cloud_cookies.txt")
                with open(temp_cookie, "w", encoding="utf-8") as f:
                    f.write(cookie_content.strip())
                return temp_cookie
    except Exception:
        pass

    return None

def normalize_youtube_url(raw_url: str) -> str:
    """
    Normaliza links do YouTube (music.youtube.com, youtu.be, shorts, etc.)
    removendo parâmetros de rastreamento (&si=..., &feature=..., etc.).
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip()
    video_id = None
    
    if "youtu.be/" in url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    elif "/shorts/" in url:
        match = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    elif "watch?" in url or "watch" in url:
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    elif "/embed/" in url or "/v/" in url:
        match = re.search(r"/(?:embed|v)/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    try:
        parsed = urlparse(url)
        netloc = "www.youtube.com" if "youtube.com" in parsed.netloc else parsed.netloc
        qs = parse_qs(parsed.query)
        v = qs.get("v", [""])[0]
        if v:
            return f"https://www.youtube.com/watch?v={v}"
        return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))
    except Exception:
        return url

def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip() or "track"

def format_duration(seconds: Optional[int]) -> str:
    """Formata segundos em MM:SS ou HH:MM:SS."""
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Obtém metadados rápidos do vídeo do YouTube sem fazer o download completo.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    cookie_path = get_cookie_file_path()

    # Tenta obter info com estratégias resilientes
    strategies = [
        # Estratégia 1: Cliente Android (mais estável e sem 403)
        {
            "player_client": ["android", "web"],
            "use_cookie": False
        },
        # Estratégia 2: Com Cookies se disponíveis
        {
            "player_client": ["web", "mweb"],
            "use_cookie": True
        }
    ]

    last_error = "Não foi possível obter dados do vídeo."

    for strat in strategies:
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "skip_download": True,
                "ffmpeg_location": get_ffmpeg_path(),
                "extractor_args": {
                    "youtube": {
                        "player_client": strat["player_client"]
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                },
                "nocheckcertificate": True,
                "geo_bypass": True,
            }

            if strat["use_cookie"] and cookie_path:
                ydl_opts["cookiefile"] = cookie_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                if info:
                    title = info.get("title", "Áudio sem título")
                    uploader = info.get("uploader") or info.get("channel", "Artista Desconhecido")
                    duration = info.get("duration", 0)
                    thumbnail = info.get("thumbnail", "")
                    view_count = info.get("view_count", 0)
                    description = info.get("description", "")

                    inferred_artist = uploader
                    inferred_title = title
                    if " - " in title:
                        parts = title.split(" - ", 1)
                        inferred_artist = parts[0].strip()
                        inferred_title = parts[1].strip()

                    clean_inferred_title = re.sub(r"\s*[\(\[](?:Official\s*(?:Music\s*)?Video|Audio|Lyric\s*Video|Clipe\s*Oficial|Video\s*Oficial)[\)\]]", "", inferred_title, flags=re.IGNORECASE).strip()

                    return {
                        "success": True,
                        "clean_url": clean_url,
                        "title": title,
                        "inferred_title": clean_inferred_title or inferred_title,
                        "inferred_artist": inferred_artist,
                        "uploader": uploader,
                        "duration": duration,
                        "duration_formatted": format_duration(duration),
                        "thumbnail": thumbnail,
                        "view_count": view_count,
                        "description": description[:300] + "..." if len(description) > 300 else description
                    }
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "success": False,
        "error": f"Erro ao processar URL: {last_error}"
    }

def download_audio_from_youtube(
    url: str,
    bitrate_kbps: int = 192,
    progress_hook=None
) -> Dict[str, Any]:
    """
    Baixa e converte o áudio do YouTube para .mp3 com a taxa de bits informada.
    Utiliza fallback multi-cliente para evitar erros 403 Forbidden e bloqueios de bot.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = tempfile.mkdtemp(prefix="music10_yt_")
    cookie_path = get_cookie_file_path()

    out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    # Lista de estratégias de download ordenadas por resiliência
    strategies = [
        # Estratégia 1: Cliente Android com formato abrangente (evita 403 Forbidden do iOS/mweb)
        {
            "format": "bestaudio/best/18/140/251",
            "player_client": ["android", "web"],
            "use_cookie": False
        },
        # Estratégia 2: Com Cookies do usuário se configurados
        {
            "format": "bestaudio/best/18/140/251",
            "player_client": ["web", "mweb", "web_creator"],
            "use_cookie": True
        },
        # Estratégia 3: Fallback padrão
        {
            "format": "ba/b/18",
            "player_client": ["android"],
            "use_cookie": False
        }
    ]

    last_error = "Falha na extração de dados do vídeo."

    for strat in strategies:
        try:
            # Limpa arquivos temporários anteriores se houver
            for item in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, item))
                except Exception:
                    pass

            ydl_opts = {
                "format": strat["format"],
                "outtmpl": out_template,
                "ffmpeg_location": ffmpeg_bin,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": str(bitrate_kbps),
                    }
                ],
                "extractor_args": {
                    "youtube": {
                        "player_client": strat["player_client"]
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                },
                "nocheckcertificate": True,
                "geo_bypass": True,
                "quiet": True,
                "no_warnings": True,
            }

            if strat["use_cookie"] and cookie_path:
                ydl_opts["cookiefile"] = cookie_path

            if progress_hook:
                ydl_opts["progress_hooks"] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                if not info:
                    continue

                mp3_files = [f for f in os.listdir(temp_dir) if f.endswith(".mp3")]
                if not mp3_files:
                    continue

                mp3_filepath = os.path.join(temp_dir, mp3_files[0])
                with open(mp3_filepath, "rb") as f:
                    audio_bytes = f.read()

                title = info.get("title", "Audio_Extraido")
                uploader = info.get("uploader") or info.get("channel", "Artista Desconhecido")
                duration = info.get("duration", 0)
                thumbnail_url = info.get("thumbnail", "")

                clean_filename = f"{sanitize_filename(title)}.mp3"

                cover_bytes = None
                if thumbnail_url:
                    try:
                        thumb_resp = requests.get(thumbnail_url, timeout=5)
                        if thumb_resp.status_code == 200:
                            cover_bytes = thumb_resp.content
                    except Exception:
                        cover_bytes = None

                inferred_artist = uploader
                inferred_title = title
                if " - " in title:
                    parts = title.split(" - ", 1)
                    inferred_artist = parts[0].strip()
                    inferred_title = parts[1].strip()

                clean_inferred_title = re.sub(r"\s*[\(\[](?:Official\s*(?:Music\s*)?Video|Audio|Lyric\s*Video|Clipe\s*Oficial|Video\s*Oficial)[\)\]]", "", inferred_title, flags=re.IGNORECASE).strip()

                return {
                    "success": True,
                    "audio_bytes": audio_bytes,
                    "filename": clean_filename,
                    "title": clean_inferred_title or inferred_title,
                    "artist": inferred_artist,
                    "uploader": uploader,
                    "duration": duration,
                    "duration_formatted": format_duration(duration),
                    "thumbnail_url": thumbnail_url,
                    "cover_bytes": cover_bytes,
                    "size_mb": round(len(audio_bytes) / (1024 * 1024), 2),
                    "bitrate": bitrate_kbps
                }

        except Exception as e:
            last_error = str(e)
            continue

    # Limpeza final
    try:
        for item in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, item))
        os.rmdir(temp_dir)
    except Exception:
        pass

    return {
        "success": False,
        "error": f"Erro durante a extração/conversão: {last_error}"
    }
