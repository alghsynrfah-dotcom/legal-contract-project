import requests
from langchain_core.embeddings import Embeddings
from shared.config import EMBEDDING_API_URL, EMBEDDING_API_KEY, EMBEDDING_MODEL

class BGEEmbeddings(Embeddings):
    def _call(self, texts):
        r = requests.post(EMBEDDING_API_URL, timeout=60,
                          headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
                          json={"model": EMBEDDING_MODEL, "input": texts})
        r.raise_for_status()
        return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
    def embed_documents(self, texts): return self._call(texts)
    def embed_query(self, text): return self._call([text])[0]
