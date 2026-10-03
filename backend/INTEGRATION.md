# ربط المشروعين (رفاه + شهد) في تطبيق واحد

## الهيكل النهائي
```
contract_ai/
  shared/            <- نسخة واحدة فقط (models, db, storage, rag_store, embeddings, errors, config)
  migrations/        <- سلسلة Alembic واحدة (0001 العقود، 0002 المحادثة، ثم تعديلات رفاه)
  app/
    main.py          <- التطبيق الوحيد (يضم الـ routers + الجدولة + CORS + معالجة الأخطاء)   [مشترك، لا يُعدَّل إلا بالاتفاق]
    routes_agent.py, agent.py, tools.py, llm.py          <- شهد
    routes_contracts.py, ingestion.py                    <- رفاه  (routes_contracts.py لازم يعرّف `router`)
  frontend/          <- رفاه
  tests/, scripts/seed_database.py
```
`main.py` بيضم `app/routes_contracts.py` تلقائياً أول ما يتواجد. التشغيل: `uvicorn app.main:app --reload` (worker واحد، لأن الجدولة داخل العملية).

## قواعد الدمج
1. `shared/` نسخة واحدة. إذا رفاه عدّلت فيها شي، تتوحد الفروقات قبل الدمج.
2. تعديل الجداول فقط عبر Alembic. رفاه تبني migration جديدة بعد `0002` (`down_revision = "0002"`) ولا تعدّل القديمة.
3. أخطاء الـ API: `raise AppError(code, message, status)` من `shared.errors`، والشكل الموحد `{"error":{"code","message"}}` بيشتغل لحاله.
4. `.env` واحد بنفس المتغيرات (`.env.example`).

## الشي الوحيد اللي لازم رفاه تستدعيه (الـ ingestion)
```python
from shared import rag_store
from app.tools import post_ingestion          # من شغل شهد

def ingest(contract_id: str):                  # يشتغل بـ BackgroundTasks بعد الرفع
    set_ingestion_status(contract_id, "processing")
    try:
        chunks = extract_and_split(contract_id)            # [{"content": "...", "page": 1}, ...]
        rag_store.add_chunks(contract_id, chunks)
        set_ingestion_status(contract_id, "ready")
        post_ingestion(contract_id)                        # يعبّي تاريخ البداية/الانتهاء والحالة فوراً
    except Exception:
        set_ingestion_status(contract_id, "failed")
```

## نقاط الاتصال مع الـ Frontend
- بعد الرفع: polling على تفاصيل العقد لحد `ingestion_status == "ready"`.
- الحالة المعروضة = `contracts.status` (Active / Expiring Soon / Expired).
- Chat: `POST /api/agent/chat` -> احفظ `session_id` لكل عقد وارسله مع كل رسالة. اعرض `sources` و`tools_used`.
- واجهة الأدوات: `GET /api/tools` و`POST /api/tools/{tool_name}`.
- لو الـ Frontend على عنوان مختلف: حدد `CORS_ORIGINS` بالـ .env.

## الـ Git (مقترح)
فرع `main` + فرع لكل واحدة (`shahd/agent`, `rafah/contracts`). أي تعديل على `shared/` أو `app/main.py` بـ Pull Request يراجعه الطرفين.
