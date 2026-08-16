"""
Music 10 - Módulo Compressor e Otimizador de Imagens (Pillow)
Permite redimensionar, comprimir e converter imagens individuais ou em lote,
gerando downloads individuais ou pacotes ZIP.
"""

import io
import os
import zipfile
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageOps

def compress_single_image(
    image_bytes: bytes,
    original_filename: str,
    quality: int = 80,
    scale_percent: int = 100,
    max_dimension: int = 0,
    output_format: str = "AUTO"
) -> Dict[str, Any]:
    """
    Comprime e redimensiona uma imagem usando Pillow.
    Retorna os bytes otimizados, dimensões e dados de redução.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Trata orientação EXIF
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        orig_w, orig_h = img.size
        orig_size_kb = len(image_bytes) / 1024.0

        # Redimensionamento
        new_w, new_h = orig_w, orig_h
        if scale_percent < 100:
            factor = scale_percent / 100.0
            new_w = max(1, int(orig_w * factor))
            new_h = max(1, int(orig_h * factor))

        if max_dimension > 0 and (new_w > max_dimension or new_h > max_dimension):
            if new_w > new_h:
                new_h = max(1, int(new_h * (max_dimension / new_w)))
                new_w = max_dimension
            else:
                new_w = max(1, int(new_w * (max_dimension / new_h)))
                new_h = max_dimension

        if (new_w, new_h) != (orig_w, orig_h):
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Determina formato de saída
        base_name, orig_ext = os.path.splitext(original_filename)
        orig_ext_clean = orig_ext.lower().replace(".", "")

        target_fmt = output_format.upper()
        if target_fmt == "AUTO":
            target_fmt = "JPEG" if orig_ext_clean in ["jpg", "jpeg"] else ("PNG" if orig_ext_clean == "png" else "WEBP")

        out_buffer = io.BytesIO()
        out_ext = ".jpg"

        if target_fmt in ["JPEG", "JPG"]:
            if img.mode in ("RGBA", "P", "LA"):
                # Converte fundo transparente para branco para JPG
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
            out_ext = ".jpg"

        elif target_fmt == "WEBP":
            img.save(out_buffer, format="WEBP", quality=quality, method=6)
            out_ext = ".webp"

        elif target_fmt == "PNG":
            # PNG usa compress_level em vez de quality
            compress_lvl = max(1, min(9, int((100 - quality) / 10)))
            img.save(out_buffer, format="PNG", optimize=True, compress_level=compress_lvl)
            out_ext = ".png"

        compressed_bytes = out_buffer.getvalue()
        new_size_kb = len(compressed_bytes) / 1024.0

        saved_kb = orig_size_kb - new_size_kb
        saved_percent = (saved_kb / orig_size_kb * 100) if orig_size_kb > 0 else 0

        new_filename = f"{base_name}_otimizada{out_ext}"

        return {
            "success": True,
            "image_bytes": compressed_bytes,
            "filename": new_filename,
            "original_size_kb": round(orig_size_kb, 1),
            "new_size_kb": round(new_size_kb, 1),
            "saved_kb": round(max(0.0, saved_kb), 1),
            "saved_percent": round(max(0.0, saved_percent), 1),
            "original_dimensions": f"{orig_w}x{orig_h}",
            "new_dimensions": f"{new_w}x{new_h}",
            "format": target_fmt
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao processar imagem: {str(e)}"
        }

def create_zip_from_images(image_results: List[Dict[str, Any]]) -> bytes:
    """Empacota múltiplos resultados de imagens em um arquivo ZIP em memória."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, res in enumerate(image_results):
            if res.get("success") and res.get("image_bytes"):
                filename = res.get("filename") or f"imagem_{idx+1}.jpg"
                zip_file.writestr(filename, res["image_bytes"])

    return zip_buffer.getvalue()
