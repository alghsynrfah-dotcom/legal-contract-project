"""File storage. Files live in STORAGE_DIR/<contract_id>/<filename>. DB stores the returned key."""
import os, shutil
from pathlib import Path
from .config import STORAGE_DIR
from .errors import AppError

def save_file(contract_id: str, filename: str, data: bytes) -> str:
    try:
        safe = Path(filename).name
        d = Path(STORAGE_DIR) / contract_id; d.mkdir(parents=True, exist_ok=True)
        (d / safe).write_bytes(data)
        return f"{contract_id}/{safe}"
    except OSError as e:
        raise AppError("STORAGE_FAILED", f"Could not save file: {e}", 500)

def get_file_path(key: str) -> Path:
    p = (Path(STORAGE_DIR) / key).resolve()
    if not str(p).startswith(str(Path(STORAGE_DIR).resolve())) or not p.exists():
        raise AppError("STORAGE_FAILED", "File not found in storage", 404)
    return p

def delete_contract_files(contract_id: str) -> None:
    shutil.rmtree(Path(STORAGE_DIR) / contract_id, ignore_errors=True)
