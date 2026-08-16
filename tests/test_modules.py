"""
Music 10 - Script de Testes Automatizados de Validação
Testa todos os módulos utilitários: FFmpeg, Audio, Imagem, iTunes API, Mutagen Tags.
"""

import os
import io
import sys
from PIL import Image

# Força UTF-8 para stdout no terminal Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import utils
from utils.ffmpeg_config import get_ffmpeg_status, get_ffmpeg_path, setup_ffmpeg
from utils.audio_processor import compress_audio, get_audio_info_from_bytes, estimate_compressed_size_mb
from utils.image_processor import compress_single_image, create_zip_from_images
from utils.tag_manager import (
    search_itunes_metadata,
    download_artwork_bytes,
    write_id3_tags_to_mp3,
    read_id3_tags_from_bytes
)
from utils.youtube_extractor import sanitize_filename, format_duration

def run_all_tests():
    print("=" * 60)
    print("🚀 INICIANDO BATERIA DE TESTES - MUSIC 10")
    print("=" * 60)

    # 1. Teste de FFmpeg
    print("\n[1/5] Testando Configuração do FFmpeg...")
    setup_ffmpeg()
    ffmpeg_status = get_ffmpeg_status()
    print(f"  -> FFmpeg Disponível: {ffmpeg_status['available']}")
    print(f"  -> Caminho: {ffmpeg_status['path']}")
    print(f"  -> Versão: {ffmpeg_status['version']}")
    assert ffmpeg_status["available"], "FFmpeg deve estar disponível!"
    print("  ✅ Teste FFmpeg: PASSOU!")

    # 2. Teste de Processamento de Áudio
    print("\n[2/5] Testando Compressor de Áudio...")
    from pydub.generators import Sine
    from pydub import AudioSegment
    
    # Gera 2 segundos de áudio sintético
    tone = Sine(440).to_audio_segment(duration=2000)
    buffer = io.BytesIO()
    tone.export(buffer, format="wav")
    wav_bytes = buffer.getvalue()
    print(f"  -> Áudio Sintético WAV gerado: {len(wav_bytes)} bytes ({len(wav_bytes)/(1024*1024):.2f} MB)")

    comp_res = compress_audio(wav_bytes, "tone_test.wav", target_bitrate_kbps=128)
    assert comp_res["success"], f"Compressão de áudio falhou: {comp_res.get('error')}"
    assert len(comp_res["audio_bytes"]) > 0, "Bytes de áudio comprimido não podem ser vazios"
    print(f"  -> MP3 128kbps gerado: {len(comp_res['audio_bytes'])} bytes ({comp_res['new_size_mb']} MB)")
    print(f"  -> Economia: {comp_res['saved_percent']}%")
    print("  ✅ Teste Compressor de Áudio: PASSOU!")

    # 3. Teste de Imagens
    print("\n[3/5] Testando Compressor de Imagens...")
    img = Image.new("RGB", (800, 800), color=(30, 144, 255))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=95)
    img_bytes = img_buf.getvalue()

    img_res = compress_single_image(img_bytes, "test_cover.jpg", quality=75, scale_percent=50, output_format="WEBP")
    assert img_res["success"], f"Compressão de imagem falhou: {img_res.get('error')}"
    assert img_res["format"] == "WEBP", "Formato deve ser WEBP"
    print(f"  -> Imagem Original: {img_res['original_size_kb']} KB ({img_res['original_dimensions']})")
    print(f"  -> Imagem Otimizada: {img_res['new_size_kb']} KB ({img_res['new_dimensions']})")
    print(f"  -> Redução: {img_res['saved_percent']}%")

    zip_bytes = create_zip_from_images([img_res])
    assert len(zip_bytes) > 0, "ZIP gerado não pode ser vazio"
    print(f"  -> Pacote ZIP gerado: {len(zip_bytes)} bytes")
    print("  ✅ Teste Compressor de Imagens: PASSOU!")

    # 4. Teste de iTunes Search API e Mutagen Tags
    print("\n[4/5] Testando iTunes Search API e Tags ID3 com Mutagen...")
    search_res = search_itunes_metadata("Bohemian Rhapsody Queen", limit=2)
    print(f"  -> Resultados obtidos no iTunes: {len(search_res)}")
    if search_res:
        top = search_res[0]
        print(f"  -> Faixa: {top['title']} | Artista: {top['artist']} | Álbum: {top['album']} | Ano: {top['year']}")
        assert top["title"] and top["artist"], "Metadados do iTunes devem conter título e artista"

    # Teste de gravação de tags ID3 e Capa no MP3 gerado
    cover_test_bytes = img_bytes
    tag_res = write_id3_tags_to_mp3(
        audio_bytes=comp_res["audio_bytes"],
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        year="1975",
        genre="Rock",
        track_num="11",
        comments="Gravado com Music 10",
        cover_bytes=cover_test_bytes
    )
    assert tag_res["success"], f"Gravação de tags falhou: {tag_res.get('error')}"
    print(f"  -> MP3 com tags e capa gerado: {tag_res['size_mb']} MB")

    # Lê de volta as tags para conferir
    read_back = read_id3_tags_from_bytes(tag_res["audio_bytes"])
    print(f"  -> Leitura de volta: Título='{read_back['title']}', Artista='{read_back['artist']}', Tem Capa={read_back['has_cover']}")
    assert read_back["title"] == "Bohemian Rhapsody", "Título ID3 lido incorreto"
    assert read_back["artist"] == "Queen", "Artista ID3 lido incorreto"
    assert read_back["has_cover"] is True, "Capa APIC não foi encontrada nas tags"
    print("  ✅ Teste Tags ID3 & iTunes API: PASSOU!")

    # 5. Teste de Funções Auxiliares
    print("\n[5/5] Testando Funções Auxiliares...")
    clean_name = sanitize_filename("Vídeo: Música Incrível / 2026? [Official] <Clip>")
    assert clean_name == "Vídeo Música Incrível  2026 [Official] Clip", f"Nome sanitizado inesperado: {clean_name}"
    
    dur_str = format_duration(3665)
    assert dur_str == "01:01:05", f"Duração inesperada: {dur_str}"
    print(f"  -> Nome Sanitizado: '{clean_name}'")
    print(f"  -> Duração Formatada: 3665s -> '{dur_str}'")
    print("  ✅ Teste Funções Auxiliares: PASSOU!")

    # 6. Teste do Renomeador de Arquivos em Lote
    print("\n[6/6] Testando Renomeador de Arquivos em Lote...")
    from utils.file_renamer import rename_sequential, rename_find_and_replace, create_zip_from_renamed_files

    dummy_files = [
        ("foto_antiga_1.jpg", b"dummy_content_1"),
        ("foto_antiga_2.jpg", b"dummy_content_2"),
        ("foto_antiga_3.jpg", b"dummy_content_3")
    ]

    # Teste sequencial
    seq_res = rename_sequential(dummy_files, base_name="img_nova", digits=3, position="prefix", separator="_")
    assert len(seq_res) == 3
    assert seq_res[0]["new_name"] == "001_img_nova.jpg"
    assert seq_res[1]["new_name"] == "002_img_nova.jpg"
    assert seq_res[2]["new_name"] == "003_img_nova.jpg"
    print("  -> Sequencial gerado:", [r["new_name"] for r in seq_res])

    # Teste find and replace (remover '_nova')
    renamed_input = [(r["new_name"], r["file_bytes"]) for r in seq_res]
    rep_res = rename_find_and_replace(renamed_input, search_text="_nova", replace_text="")
    assert rep_res[0]["new_name"] == "001_img.jpg"
    assert rep_res[1]["new_name"] == "002_img.jpg"
    assert rep_res[2]["new_name"] == "003_img.jpg"
    print("  -> Find & Replace gerado:", [r["new_name"] for r in rep_res])

    # Teste ZIP
    renamed_zip = create_zip_from_renamed_files(rep_res)
    assert len(renamed_zip) > 0
    print(f"  -> ZIP de arquivos renomeados: {len(renamed_zip)} bytes")
    print("  ✅ Teste Renomeador de Arquivos: PASSOU!")

    print("\n" + "=" * 60)
    print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
