from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.settings import settings
from api.endpoints.health import router as health_router
from api.endpoints.sessions import router as sessions_router
from api.endpoints.traces import router as traces_router
from api.endpoints.rules import router as rules_router
from api.db import get_db
from api.verifier_store import store

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if getattr(settings, "frontend_origin", None):
    origins.append(settings.frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_rules_on_startup():
    # Load rules from DB once the app starts
    try:
        from fastapi import Depends
        # Manual session since startup hook cannot use Depends directly
        from api.db import SessionLocal
        db = SessionLocal()
        try:
            store.load_from_db(db)
        finally:
            db.close()
    except Exception:
        # Keep default verifier on failure
        store.get()

@app.get("/")
def index():
    return {
        "name": settings.app_name,
        "status": "ok",
        "endpoints": ["/healthz", "/sessions", "/traces", "/rules"],
    }

# Simple reload endpoint
@app.post("/rules/reload")
def reload_rules():
    from api.db import SessionLocal
    db = SessionLocal()
    try:
        v = store.load_from_db(db)
        return {"ok": True, "count": len(v.rules)}
    finally:
        db.close()

# Routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(traces_router)
app.include_router(rules_router)
