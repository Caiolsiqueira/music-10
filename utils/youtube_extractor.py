"""
Music 10 - Módulo Extrator de YouTube para MP3 (yt-dlp + FFmpeg)
Permite obter informações rápidas de vídeos e extrair áudio com bitrate configurável,
com suporte a bypass de bot do YouTube e URLs do YouTube Music.
"""

import os
import re
import tempfile
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse
from .ffmpeg_config import get_ffmpeg_path

def normalize_youtube_url(raw_url: str) -> str:
    """
    Normaliza links do YouTube (music.youtube.com, youtu.be, shorts, etc.)
    removendo parâmetros de rastreamento (&si=..., &feature=..., etc.).
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip()
    
    # Extrai o video ID
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
            
    # watch?v=ID (em youtube.com ou music.youtube.com)
    elif "watch?" in url or "watch" in url:
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
            
    # /embed/ID ou /v/ID
    elif "/embed/" in url or "/v/" in url:
        match = re.search(r"/(?:embed|v)/([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    # Fallback: remove query parameters não essenciais
    try:
        parsed = urlparse(url)
        # Substitui music.youtube.com por www.youtube.com
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
    Utiliza clientes android/ios para contornar verificações de bot.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "ffmpeg_location": get_ffmpeg_path(),
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"]
            }
        },
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

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

            # Tenta identificar se o título possui formato "Artista - Música"
            inferred_artist = uploader
            inferred_title = title
            if " - " in title:
                parts = title.split(" - ", 1)
                inferred_artist = parts[0].strip()
                inferred_title = parts[1].strip()

            # Limpa sufixos comuns em títulos de clipes como (Official Video), [Audio], etc.
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
        err_msg = str(e)
        if "Sign in to confirm" in err_msg or "bot" in err_msg.lower():
            err_msg = "O YouTube solicitou verificação para esta URL. Tente novamente em instantes."
        return {
            "success": False,
            "error": f"Erro ao processar URL: {err_msg}"
        }

def download_audio_from_youtube(
    url: str,
    bitrate_kbps: int = 192,
    progress_hook=None
) -> Dict[str, Any]:
    """
    Baixa e converte o áudio do YouTube para .mp3 com a taxa de bits informada.
    Lê os bytes na memória e remove com segurança todos os arquivos temporários.
    """
    import yt_dlp

    clean_url = normalize_youtube_url(url)
    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = tempfile.mkdtemp(prefix="music10_yt_")

    out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "ba/b",
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
                "player_client": ["android", "ios", "mweb", "web"]
            }
        },
        "nocheckcertificate": True,
        "geo_bypass": True,
        "quiet": True,
        "no_warnings": True,
    }

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            if not info:
                return {"success": False, "error": "Falha na extração de dados do vídeo."}

            title = info.get("title", "Audio_Extraido")
            uploader = info.get("uploader") or info.get("channel", "Artista Desconhecido")
            duration = info.get("duration", 0)
            thumbnail_url = info.get("thumbnail", "")

            # Encontra o arquivo mp3 gerado no diretório temporário
            mp3_files = [f for f in os.listdir(temp_dir) if f.endswith(".mp3")]
            if not mp3_files:
                return {"success": False, "error": "O arquivo MP3 não foi gerado pelo conversor."}

            mp3_filepath = os.path.join(temp_dir, mp3_files[0])
            with open(mp3_filepath, "rb") as f:
                audio_bytes = f.read()

            clean_filename = f"{sanitize_filename(title)}.mp3"

            # Tenta baixar a imagem da thumbnail para carregar como capa inicial
            cover_bytes = None
            if thumbnail_url:
                try:
                    thumb_resp = requests.get(thumbnail_url, timeout=5)
                    if thumb_resp.status_code == 200:
                        cover_bytes = thumb_resp.content
                except Exception:
                    cover_bytes = None

            # Tenta inferir artista e título
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
        err_msg = str(e)
        if "Sign in to confirm" in err_msg or "bot" in err_msg.lower():
            err_msg = "O YouTube bloqueou temporariamente a requisição com verificação de bot. Tente novamente em alguns segundos."
        return {
            "success": False,
            "error": f"Erro durante a extração/conversão: {err_msg}"
        }
    finally:
        # Limpa o diretório temporário
        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
            os.rmdir(temp_dir)
        except Exception:
            pass
