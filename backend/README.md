# AI Legal Contract Management

## Setup
1. PostgreSQL 13+ (or `docker compose up -d db`). No extensions needed..
2. `cp .env.example .env` and fill values.
3. `pip install -r requirements.txt`
4. `alembic upgrade head`   (creates all tables + vector index)
5. `uvicorn app.main:app --reload`

## Shared contract (Rafah <-> Shahd)
- DB models: `shared/models.py` (`contract_id` = UUID string everywhere). Schema changes ONLY via `alembic revision`.
- Files: `shared.storage.save_file(contract_id, filename, bytes)` -> store returned key in `contracts.file_path`.
- Ingestion (Rafah): after upload set `ingestion_status='processing'`, then
  `shared.rag_store.add_chunks(contract_id, [{"content":..., "page":...}])`, then `'ready'` (or `'failed'`).
- Tools/Agent (Shahd) read chunks only via `shared.rag_store.retrieve_chunks`.
- Status (`Active|Expiring Soon|Expired`) and `start_date/end_date` are written by Shahd's tools/daily job; Rafah only reads them.
- Errors: raise `shared.errors.AppError(code, message, status)`; API returns `{"error":{"code","message"}}`.
- Shahd's endpoints: `POST /api/agent/chat`, `GET /api/tools`, `POST /api/tools/{tool_name}`.

## Agent chat memory
`POST /api/agent/chat {contract_id, message, session_id?}` -> returns `session_id`; send it back on the next message to keep context.
`GET /api/agent/chat/{session_id}?contract_id=...` (history), `DELETE /api/agent/chat/{session_id}` (new conversation).
Schema: migration `0002` (`chat_messages`). Run `alembic upgrade head` after pulling.

## Tests (no DB / LLM needed)
`pip install -r requirements-dev.txt && pytest -q`
