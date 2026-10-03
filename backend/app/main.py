"""The ONE FastAPI app. Run: uvicorn app.main:app --reload   (use a single worker: the scheduler runs in-process)"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from shared.errors import AppError
from .tools import check_expirations, daily_job
from .routes_agent import router as agent_router

@asynccontextmanager
async def lifespan(app):
    sch = BackgroundScheduler()
    sch.add_job(daily_job, "cron", hour=2, minute=0, id="daily_job")  # daily 02:00: dates extraction + status update
    sch.start(); check_expirations()
    yield
    sch.shutdown()

app = FastAPI(title="AI Legal Contract Management", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(AppError)
async def app_error_handler(_, e: AppError):
    return JSONResponse(status_code=e.status, content={"error": {"code": e.code, "message": e.message}})

@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, e: RequestValidationError):
    msg = "; ".join(f"{'.'.join(str(x) for x in err['loc'][1:])}: {err['msg']}" for err in e.errors())
    return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST", "message": msg}})

app.include_router(agent_router)  # Shahd: agent + tools

# Rafah: upload / list / search / details live in app/routes_contracts.py and must expose `router`.
try:
    from .routes_contracts import router as contracts_router
    app.include_router(contracts_router)
except ModuleNotFoundError as e:
    if e.name != "app.routes_contracts": raise
