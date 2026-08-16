"""
Music 10 - Módulo de Tags ID3 e Busca na iTunes Search API (Mutagen)
Permite buscar metadados e capas oficiais na iTunes API e embutir tags ID3v2
(Título, Artista, Álbum, Ano, Gênero, Faixa, Capa APIC) em arquivos .mp3.
"""

import io
import os
import tempfile
import requests
from typing import Dict, Any, List, Optional
import mutagen
from mutagen.id3 import (
    ID3,
    TIT2,
    TPE1,
    TALB,
    TDRC,
    TYER,
    TCON,
    TRCK,
    COMM,
    APIC,
    ID3NoHeaderError,
)

def search_itunes_metadata(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Busca metadados oficiais e capas na iTunes Search API (Pública e Gratuita).
    Retorna lista estruturada de faixas com capas em alta resolução.
    """
    if not query or not query.strip():
        return []

    url = "https://itunes.apple.com/search"
    params = {
        "term": query.strip(),
        "entity": "song",
        "media": "music",
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return []

        data = response.json()
        results = []

        for item in data.get("results", []):
            raw_artwork = item.get("artworkUrl100", "")
            # Substitui por resolução alta (600x600 ou 1000x1000)
            high_res_artwork = raw_artwork.replace("100x100bb", "600x600bb") if raw_artwork else ""
            ultra_res_artwork = raw_artwork.replace("100x100bb", "1200x1200bb") if raw_artwork else ""

            # Extrai ano do releaseDate
            release_date = item.get("releaseDate", "")
            year = release_date[:4] if release_date and len(release_date) >= 4 else ""

            results.append({
                "track_id": item.get("trackId"),
                "title": item.get("trackName", ""),
                "artist": item.get("artistName", ""),
                "album": item.get("collectionName", ""),
                "year": year,
                "genre": item.get("primaryGenreName", ""),
                "track_number": str(item.get("trackNumber", "")),
                "track_count": str(item.get("trackCount", "")),
                "artwork_url": high_res_artwork,
                "artwork_ultra_url": ultra_res_artwork,
                "preview_url": item.get("previewUrl", "")
            })

        return results
    except Exception:
        return []

def download_artwork_bytes(artwork_url: str) -> Optional[bytes]:
    """Baixa os bytes da imagem de capa a partir de uma URL."""
    if not artwork_url:
        return None
    try:
        resp = requests.get(artwork_url, timeout=10)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None

def read_id3_tags_from_bytes(audio_bytes: bytes) -> Dict[str, Any]:
    """Lê metadados e capa existentes em um buffer de MP3."""
    result = {
        "title": "",
        "artist": "",
        "album": "",
        "year": "",
        "genre": "",
        "track_num": "",
        "comments": "",
        "has_cover": False,
        "cover_bytes": None,
        "cover_mime": "image/jpeg"
    }

    try:
        audio_file = io.BytesIO(audio_bytes)
        tags = ID3(audio_file)

        if "TIT2" in tags:
            result["title"] = str(tags["TIT2"])
        if "TPE1" in tags:
            result["artist"] = str(tags["TPE1"])
        if "TALB" in tags:
            result["album"] = str(tags["TALB"])
        if "TDRC" in tags:
            result["year"] = str(tags["TDRC"])
        elif "TYER" in tags:
            result["year"] = str(tags["TYER"])
        if "TCON" in tags:
            result["genre"] = str(tags["TCON"])
        if "TRCK" in tags:
            result["track_num"] = str(tags["TRCK"])
        if "COMM::eng" in tags:
            result["comments"] = str(tags["COMM::eng"])
        elif "COMM" in tags:
            result["comments"] = str(tags["COMM"])

        # Extrai capa se houver
        for key in tags.keys():
            if key.startswith("APIC"):
                apic_frame = tags[key]
                result["has_cover"] = True
                result["cover_bytes"] = apic_frame.data
                result["cover_mime"] = apic_frame.mime
                break

    except (ID3NoHeaderError, Exception):
        pass

    return result

def write_id3_tags_to_mp3(
    audio_bytes: bytes,
    title: str = "",
    artist: str = "",
    album: str = "",
    year: str = "",
    genre: str = "",
    track_num: str = "",
    comments: str = "",
    cover_bytes: Optional[bytes] = None,
    cover_mime: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Grava metadados ID3v2 e embuti a capa do álbum diretamente no arquivo MP3.
    Retorna os bytes do áudio com tags aplicadas.
    """
    temp_file = None
    try:
        # Cria arquivo temporário para escrita com mutagen
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            tags = ID3(temp_path)
        except ID3NoHeaderError:
            tags = ID3()

        # Atualiza frames ID3v2
        if title:
            tags.add(TIT2(encoding=3, text=title))
        if artist:
            tags.add(TPE1(encoding=3, text=artist))
        if album:
            tags.add(TALB(encoding=3, text=album))
        if year:
            tags.add(TDRC(encoding=3, text=str(year)))
        if genre:
            tags.add(TCON(encoding=3, text=genre))
        if track_num:
            tags.add(TRCK(encoding=3, text=str(track_num)))
        if comments:
            tags.add(COMM(encoding=3, lang="por", desc="Desc", text=comments))

        # Adiciona capa se fornecida
        if cover_bytes:
            # Remove capas antigas para evitar duplicidade
            for key in list(tags.keys()):
                if key.startswith("APIC"):
                    del tags[key]

            # Detecta mime type
            mime_type = cover_mime or "image/jpeg"
            if cover_bytes.startswith(b"\x89PNG"):
                mime_type = "image/png"
            elif cover_bytes.startswith(b"RIFF") and b"WEBP" in cover_bytes[:12]:
                mime_type = "image/webp"

            tags.add(
                APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,  # Front Cover
                    desc="Cover",
                    data=cover_bytes
                )
            )

        tags.save(temp_path, v2_version=3)

        with open(temp_path, "rb") as f:
            tagged_audio_bytes = f.read()

        return {
            "success": True,
            "audio_bytes": tagged_audio_bytes,
            "has_cover": cover_bytes is not None,
            "size_mb": round(len(tagged_audio_bytes) / (1024 * 1024), 2)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao gravar tags ID3: {str(e)}"
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
