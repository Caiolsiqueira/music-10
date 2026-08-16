"""
Music 10 - Módulo Compressor e Conversor de Áudio (pydub + FFmpeg)
Permite carregar arquivos em múltiplos formatos (.mp3, .wav, .m4a, .ogg)
e re-codificar com controle preciso de bitrate e redução de tamanho.
"""

import io
import os
import tempfile
from typing import Dict, Any, Tuple
from .ffmpeg_config import get_ffmpeg_path

def get_audio_info_from_bytes(file_bytes: bytes, ext: str = "mp3") -> Dict[str, Any]:
    """Obtém duração, canais e taxa de amostragem de um áudio em memória."""
    from pydub import AudioSegment
    get_ffmpeg_path()

    ext_clean = ext.lower().replace(".", "").strip()
    if ext_clean == "m4a":
        ext_clean = "mp4"

    try:
        segment = AudioSegment.from_file(io.BytesIO(file_bytes), format=ext_clean)
        duration_sec = len(segment) / 1000.0
        channels = segment.channels
        frame_rate = segment.frame_rate
        size_mb = len(file_bytes) / (1024 * 1024)

        return {
            "success": True,
            "duration_sec": duration_sec,
            "channels": channels,
            "frame_rate": frame_rate,
            "size_mb": round(size_mb, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao ler informações de áudio: {str(e)}"
        }

def estimate_compressed_size_mb(duration_sec: float, bitrate_kbps: int) -> float:
    """Estima o tamanho aproximado do arquivo final em MB."""
    if duration_sec <= 0:
        return 0.0
    bytes_est = (duration_sec * bitrate_kbps * 1000) / 8
    mb_est = bytes_est / (1024 * 1024)
    return round(mb_est, 2)

def compress_audio(
    file_bytes: bytes,
    original_filename: str,
    target_bitrate_kbps: int = 128,
    to_mono: bool = False,
    sample_rate: int = 44100
) -> Dict[str, Any]:
    """
    Comprime e re-codifica o áudio para formato MP3 com o bitrate selecionado.
    Retorna os bytes do MP3 processado e métricas comparativas.
    """
    from pydub import AudioSegment
    get_ffmpeg_path()

    ext = os.path.splitext(original_filename)[1].lower().replace(".", "").strip()
    if not ext:
        ext = "mp3"
    format_in = "mp4" if ext == "m4a" else ext

    try:
        segment = AudioSegment.from_file(io.BytesIO(file_bytes), format=format_in)

        if to_mono and segment.channels > 1:
            segment = segment.set_channels(1)

        if sample_rate and sample_rate != segment.frame_rate:
            segment = segment.set_frame_rate(sample_rate)

        duration_sec = len(segment) / 1000.0
        bitrate_str = f"{target_bitrate_kbps}k"

        # Exporta para buffer de memória em formato MP3
        out_buffer = io.BytesIO()
        segment.export(
            out_buffer,
            format="mp3",
            bitrate=bitrate_str,
            parameters=["-q:a", "2"]
        )

        compressed_bytes = out_buffer.getvalue()
        original_size_mb = len(file_bytes) / (1024 * 1024)
        new_size_mb = len(compressed_bytes) / (1024 * 1024)

        reduction_mb = original_size_mb - new_size_mb
        reduction_percent = (reduction_mb / original_size_mb * 100) if original_size_mb > 0 else 0

        base_name = os.path.splitext(original_filename)[0]
        new_filename = f"{base_name}_{target_bitrate_kbps}kbps.mp3"

        return {
            "success": True,
            "audio_bytes": compressed_bytes,
            "filename": new_filename,
            "original_size_mb": round(original_size_mb, 2),
            "new_size_mb": round(new_size_mb, 2),
            "saved_mb": round(max(0.0, reduction_mb), 2),
            "saved_percent": round(max(0.0, reduction_percent), 1),
            "duration_sec": round(duration_sec, 1),
            "bitrate": target_bitrate_kbps
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Erro durante a compressão de áudio: {str(e)}"
        }
