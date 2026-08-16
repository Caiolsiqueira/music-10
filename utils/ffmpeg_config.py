"""
Music 10 - Configuração e Detecção Autônoma de FFmpeg
Garante que o FFmpeg esteja sempre disponível para yt-dlp e pydub,
seja pelo PATH do sistema ou pelo binário embutido do imageio-ffmpeg.
"""

import os
import shutil
import subprocess
from typing import Optional

_FFMPEG_PATH: Optional[str] = None

def setup_ffmpeg() -> str:
    """
    Detecta e configura o caminho do executável do FFmpeg.
    Injeta o caminho no PATH do ambiente e configura o pydub.
    Retorna o caminho do executável FFmpeg válido.
    """
    global _FFMPEG_PATH
    if _FFMPEG_PATH and os.path.exists(_FFMPEG_PATH):
        return _FFMPEG_PATH

    # 1. Tenta encontrar 'ffmpeg' no PATH do sistema
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        _FFMPEG_PATH = sys_ffmpeg
    else:
        # 2. Tenta obter via imageio-ffmpeg
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_exe and os.path.exists(ffmpeg_exe):
                _FFMPEG_PATH = ffmpeg_exe
                # Adiciona o diretório do binário ao PATH para que sub-processos encontrem
                bin_dir = os.path.dirname(ffmpeg_exe)
                if bin_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        except Exception:
            _FFMPEG_PATH = "ffmpeg"

    # Configura o pydub se disponível
    try:
        import pydub.utils
        from pydub import AudioSegment
        if _FFMPEG_PATH and os.path.exists(_FFMPEG_PATH):
            AudioSegment.converter = _FFMPEG_PATH
            AudioSegment.ffmpeg = _FFMPEG_PATH
            # Patch pydub.utils.which
            _orig_which = pydub.utils.which
            def _custom_which(program):
                if program in ["ffmpeg", "avconv"]:
                    return _FFMPEG_PATH
                return _orig_which(program)
            pydub.utils.which = _custom_which
    except Exception:
        pass

    return _FFMPEG_PATH or "ffmpeg"

def get_ffmpeg_path() -> str:
    """Retorna o caminho absoluto do executável FFmpeg."""
    return setup_ffmpeg()

def get_ffmpeg_status() -> dict:
    """Retorna informações de status do FFmpeg para a UI."""
    exe_path = get_ffmpeg_path()
    available = False
    version = "Desconhecida"

    if exe_path and (os.path.exists(exe_path) or shutil.which(exe_path)):
        try:
            res = subprocess.run([exe_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0:
                available = True
                first_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg Ativo"
                version = first_line.split("Copyright")[0].strip()
        except Exception as e:
            available = False
            version = f"Erro: {str(e)}"

    return {
        "available": available,
        "path": exe_path,
        "version": version
    }

# Executa setup no import
setup_ffmpeg()
