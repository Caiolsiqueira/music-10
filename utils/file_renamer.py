"""
Music 10 - Módulo Organizador e Renomeador de Arquivos em Lote
Permite renomeação sequencial padronizada (ex: 001_img_nova.jpg) e
remoção/substituição de trechos de texto em lote com exportação em ZIP.
"""

import io
import os
import re
import zipfile
from typing import List, Dict, Any, Tuple

def rename_sequential(
    files: List[Tuple[str, bytes]],
    base_name: str = "arquivo",
    digits: int = 3,
    position: str = "prefix",
    separator: str = "_",
    start_index: int = 1
) -> List[Dict[str, Any]]:
    """
    Renomeia uma lista de arquivos de forma sequencial padronizada.
    Exemplo (prefix): 001_img_nova.jpg, 002_img_nova.jpg
    Exemplo (suffix): img_nova_001.jpg, img_nova_002.jpg
    """
    results = []
    
    for idx, (orig_filename, file_bytes) in enumerate(files, start=start_index):
        orig_base, ext = os.path.splitext(orig_filename)
        number_str = str(idx).zfill(digits)
        
        clean_base = base_name.strip()
        if not clean_base:
            clean_base = "item"

        if position == "prefix":
            new_name = f"{number_str}{separator}{clean_base}{ext}"
        else:
            new_name = f"{clean_base}{separator}{number_str}{ext}"

        results.append({
            "original_name": orig_filename,
            "new_name": new_name,
            "file_bytes": file_bytes,
            "size_kb": round(len(file_bytes) / 1024.0, 1),
            "ext": ext
        })

    return results

def rename_find_and_replace(
    files: List[Tuple[str, bytes]],
    search_text: str = "",
    replace_text: str = "",
    case_sensitive: bool = False,
    clean_spaces: bool = False,
    case_mode: str = "none"  # "none", "lower", "upper", "title"
) -> List[Dict[str, Any]]:
    """
    Localiza um texto/termo específico no nome dos arquivos e o deleta ou substitui.
    Exemplo: remover '_nova' de '001_img_nova.jpg' -> '001_img.jpg'
    """
    results = []

    for orig_filename, file_bytes in files:
        orig_base, ext = os.path.splitext(orig_filename)
        new_base = orig_base

        if search_text:
            if case_sensitive:
                new_base = new_base.replace(search_text, replace_text)
            else:
                pattern = re.compile(re.escape(search_text), re.IGNORECASE)
                new_base = pattern.sub(replace_text, new_base)

        if clean_spaces:
            # Substitui múltiplos espaços por um único
            new_base = re.sub(r"\s+", " ", new_base).strip()
            # Remove underlines duplos ou traços duplos se gerados
            new_base = re.sub(r"_{2,}", "_", new_base)
            new_base = re.sub(r"-{2,}", "-", new_base)

        if case_mode == "lower":
            new_base = new_base.lower()
        elif case_mode == "upper":
            new_base = new_base.upper()
        elif case_mode == "title":
            new_base = new_base.title()

        new_name = f"{new_base}{ext}"

        results.append({
            "original_name": orig_filename,
            "new_name": new_name,
            "file_bytes": file_bytes,
            "size_kb": round(len(file_bytes) / 1024.0, 1),
            "ext": ext
        })

    return results

def create_zip_from_renamed_files(results: List[Dict[str, Any]]) -> bytes:
    """Empacota os arquivos renomeados em um arquivo ZIP em memória."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in results:
            new_name = item.get("new_name") or "arquivo"
            zip_file.writestr(new_name, item["file_bytes"])

    return zip_buffer.getvalue()
