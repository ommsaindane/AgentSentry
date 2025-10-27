from fastapi import FastAPI
from api.settings import settings
from api.endpoints.health import router as health_router
from api.endpoints.sessions import router as sessions_router
from api.endpoints.traces import router as traces_router

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(traces_router)
