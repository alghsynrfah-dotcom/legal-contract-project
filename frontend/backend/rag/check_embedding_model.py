import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    base_url=os.getenv("EMBEDDING_API_URL"),
    api_key=os.getenv("EMBEDDING_API_KEY")
)


models = client.models.list()

print("\n========== EMBEDDING MODELS ==========")

for model in models.data:
    print(model.id)