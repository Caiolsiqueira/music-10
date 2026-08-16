"""
Music 10 - Pacote de Módulos Utilitários
Inicializa automaticamente o ambiente e o FFmpeg.
"""

from .ffmpeg_config import setup_ffmpeg

# Configura o FFmpeg no PATH antes de outros módulos serem carregados
setup_ffmpeg()
