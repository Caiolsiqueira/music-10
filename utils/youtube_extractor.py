"""
Music 10 - Módulo Extrator de YouTube para MP3 (yt-dlp + FFmpeg)
Permite obter informações rápidas de vídeos e extrair áudio com bitrate configurável,
com suporte multiplataforma (Linux / Windows) utilizando pathlib e tempfile.
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

# Cabeçalhos HTTP modernos e realistas para mitigar bloqueios de nuvem
DEFAULT_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Mode": "navigate",
}

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

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Obtém metadados rápidos do vídeo do YouTube sem fazer o download completo.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "ffmpeg_location": ffmpeg_bin if ffmpeg_bin and ffmpeg_bin != "ffmpeg" else None,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "http_headers": DEFAULT_HTTP_HEADERS,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    # Remove chaves com valor None
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
    Utiliza pathlib.Path e tempfile para total compatibilidade entre Windows e Linux.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()
    
    # Cria diretório temporário agnóstico ao SO
    temp_dir = Path(tempfile.mkdtemp(prefix="music10_yt_"))
    out_template = str(temp_dir / "%(title)s.%(ext)s")

    format_list = [
        "18",
        "best[height<=480]",
        "best[height<=720]",
        "best"
    ]

    last_error = "Falha na extração de dados do vídeo."

    for fmt in format_list:
        try:
            # Limpa arquivos residuais do diretório temporário
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink(missing_ok=True)

            ydl_opts = {
                "format": fmt,
                "outtmpl": out_template,
                "ffmpeg_location": ffmpeg_bin if ffmpeg_bin and ffmpeg_bin != "ffmpeg" else None,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": str(bitrate_kbps),
                    }
                ],
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },
                "http_headers": DEFAULT_HTTP_HEADERS,
                "nocheckcertificate": True,
                "geo_bypass": True,
                "quiet": True,
                "no_warnings": True,
            }

            ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

            if progress_hook:
                ydl_opts["progress_hooks"] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                if not info:
                    continue

                mp3_files = list(temp_dir.glob("*.mp3"))
                if not mp3_files:
                    continue

                mp3_filepath = mp3_files[0]
                audio_bytes = mp3_filepath.read_bytes()

                title = info.get("title", "Audio_Extraido")
                uploader = info.get("uploader") or info.get("channel", "Artista Desconhecido")
                duration = info.get("duration", 0)
                thumbnail_url = info.get("thumbnail", "")

                clean_filename = f"{sanitize_filename(title)}.mp3"

                cover_bytes = None
                if thumbnail_url:
                    try:
                        thumb_resp = requests.get(thumbnail_url, headers=DEFAULT_HTTP_HEADERS, timeout=5)
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

    # Limpeza segura do diretório temporário
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return {
        "success": False,
        "error": f"Erro durante a extração/conversão: {last_error}"
    }
