import os
from dotenv import load_dotenv
load_dotenv()

def _req(name):
    v = os.getenv(name)
    if not v: raise RuntimeError(f"Missing required environment variable: {name}")
    return v

DATABASE_URL = _req("DATABASE_URL")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
EMBEDDING_API_URL = _req("EMBEDDING_API_URL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL-72B-Instruct")
VLLM_API_URL = _req("VLLM_API_URL")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
EXPIRING_SOON_DAYS = int(os.getenv("EXPIRING_SOON_DAYS", "30"))
