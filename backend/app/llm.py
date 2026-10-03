import json, re
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from shared.config import MODEL_NAME, VLLM_API_URL, VLLM_API_KEY
from shared.errors import AppError

llm = ChatOpenAI(model=MODEL_NAME, base_url=VLLM_API_URL, api_key=VLLM_API_KEY, temperature=0)

def extract_structured(schema: type[BaseModel], instruction: str, context: str) -> BaseModel:
    """Structured Output via JSON prompt + Pydantic validation (works without server-side guided decoding)."""
    prompt = (f"{instruction}\n\nReturn ONLY valid JSON matching this schema, no extra text:\n"
              f"{json.dumps(schema.model_json_schema())}\n\nContract excerpts:\n{context}")
    try:
        raw = llm.invoke(prompt).content
        m = re.search(r"\{.*\}", raw, re.S)
        return schema.model_validate_json(m.group(0))
    except Exception as e:
        raise AppError("EXTRACTION_FAILED", f"Could not extract structured data: {e}", 502)
