"""
Music 10 - Módulo Extrator de YouTube para MP3 (yt-dlp + FFmpeg + API Fallback)
Extração híbrida com yt-dlp local/nuvem e fallback via APIs externas para garantir
máxima resiliência contra bloqueios de Data Center (403 Forbidden).
"""

import os
import re
import shutil
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse
from .ffmpeg_config import get_ffmpeg_path

# Cabeçalhos HTTP Android oficiais para mitigar bloqueios de Data Center
ANDROID_HTTP_HEADERS = {
    "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
    "Accept-Language": "en-US,en;q=0.9",
}

def normalize_youtube_url(raw_url: str) -> str:
    """
    Normaliza links do YouTube (music.youtube.com, youtu.be, shorts, etc.)
    removendo estritamente qualquer parâmetro (&list=..., &start_radio=..., &si=..., &index=..., etc.)
    e retornando unicamente no formato: https://www.youtube.com/watch?v=ID_DO_VIDEO
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip()
    video_id = None
    
    # youtu.be/ID
    if "youtu.be/" in url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    # /shorts/ID
    elif "/shorts/" in url:
        match = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    # /embed/ID ou /v/ID
    elif "/embed/" in url or "/v/" in url:
        match = re.search(r"/(?:embed|v)/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
    # watch?v=ID ou music.youtube.com/watch?v=ID
    elif "v=" in url:
        match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    match = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"

    return url

def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos em qualquer SO."""
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

def download_audio_via_cobalt(youtube_url: str, bitrate_kbps: int = 192) -> Optional[bytes]:
    """
    Fallback de conversão via instâncias públicas do Cobalt API.
    """
    api_endpoints = [
        "https://api.cobalt.tools/api/json",
        "https://api.cobalt.tools/",
        "https://co.eepy.today/api/json"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "url": youtube_url,
        "downloadMode": "audio",
        "audioFormat": "mp3",
        "audioBitrate": str(bitrate_kbps)
    }
    
    for endpoint in api_endpoints:
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                download_url = data.get("url") or (data.get("stream") if isinstance(data.get("stream"), str) else None)
                if download_url:
                    audio_response = requests.get(download_url, timeout=30)
                    if audio_response.status_code == 200 and len(audio_response.content) > 1000:
                        return audio_response.content
        except Exception:
            continue
            
    return None

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Obtém metadados rápidos do vídeo do YouTube sem fazer o download completo.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()

    ydl_opts = {
        "format": "bestaudio/best/18",
        "skip_download": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ffmpeg_location": ffmpeg_bin if ffmpeg_bin and ffmpeg_bin != "ffmpeg" else None,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "http_headers": ANDROID_HTTP_HEADERS
    }

    ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                return {"success": False, "error": "Não foi possível obter dados do vídeo."}

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
        return {
            "success": False,
            "error": f"Erro ao processar URL: {str(e)}"
        }

def download_audio_from_youtube(
    url: str,
    bitrate_kbps: int = 192,
    progress_hook=None
) -> Dict[str, Any]:
    """
    Baixa e converte o áudio do YouTube para .mp3 com a taxa de bits informada.
    Utiliza yt-dlp e conta com fallback automático para garantir 100% de sucesso.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()
    
    temp_dir = Path(tempfile.mkdtemp(prefix="music10_yt_"))
    out_template = str(temp_dir / "%(title)s.%(ext)s")

    # Obtém dados prévios para título e thumbnail
    meta_info = extract_video_info(clean_url)
    fallback_title = meta_info.get("title", "Audio_Extraido") if meta_info.get("success") else "Audio_Extraido"
    fallback_artist = meta_info.get("inferred_artist", "") if meta_info.get("success") else ""
    fallback_thumb = meta_info.get("thumbnail", "") if meta_info.get("success") else ""
    fallback_dur = meta_info.get("duration", 0) if meta_info.get("success") else 0

    ydl_opts = {
        "format": "bestaudio/best/18",
        "outtmpl": out_template,
        "ffmpeg_location": ffmpeg_bin if ffmpeg_bin and ffmpeg_bin != "ffmpeg" else None,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(bitrate_kbps),
            }
        ],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb"],
                "player_skip": ["webpage", "configs"]
            }
        },
        "http_headers": ANDROID_HTTP_HEADERS
    }

    ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            if info:
                mp3_files = list(temp_dir.glob("*.mp3"))
                if mp3_files:
                    mp3_filepath = mp3_files[0]
                    audio_bytes = mp3_filepath.read_bytes()

                    title = info.get("title", fallback_title)
                    uploader = info.get("uploader") or info.get("channel", fallback_artist)
                    duration = info.get("duration", fallback_dur)
                    thumbnail_url = info.get("thumbnail", fallback_thumb)

                    clean_filename = f"{sanitize_filename(title)}.mp3"

                    cover_bytes = None
                    if thumbnail_url:
                        try:
                            thumb_resp = requests.get(thumbnail_url, headers=ANDROID_HTTP_HEADERS, timeout=5)
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

    except Exception as yt_err:
        # Tenta fallback via Cobalt API
        try:
            cobalt_bytes = download_audio_via_cobalt(clean_url, bitrate_kbps=bitrate_kbps)
            if cobalt_bytes:
                clean_filename = f"{sanitize_filename(fallback_title)}.mp3"
                
                cover_bytes = None
                if fallback_thumb:
                    try:
                        thumb_resp = requests.get(fallback_thumb, headers=ANDROID_HTTP_HEADERS, timeout=5)
                        if thumb_resp.status_code == 200:
                            cover_bytes = thumb_resp.content
                    except Exception:
                        cover_bytes = None

                return {
                    "success": True,
                    "audio_bytes": cobalt_bytes,
                    "filename": clean_filename,
                    "title": fallback_title,
                    "artist": fallback_artist,
                    "uploader": fallback_artist,
                    "duration": fallback_dur,
                    "duration_formatted": format_duration(fallback_dur),
                    "thumbnail_url": fallback_thumb,
                    "cover_bytes": cover_bytes,
                    "size_mb": round(len(cobalt_bytes) / (1024 * 1024), 2),
                    "bitrate": bitrate_kbps
                }
        except Exception:
            pass

        return {
            "success": False,
            "error": f"Erro durante a extração/conversão: {str(yt_err)}"
        }
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
