import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database.database import init_db
from backend.app.execution.task_manager import task_manager
from backend.app.api.ws import router as ws_router, ws_manager

from backend.app.api.terminal import router as terminal_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.files import router as files_router
from backend.app.api.system import router as system_router
from backend.app.api.history import router as history_router
from backend.app.api.workflows import router as workflows_router
from backend.app.api.settings import router as settings_router
from backend.app.api.drives import router as drives_router
from backend.app.api.simulators import router as simulators_router
from backend.app.api.digital_twin import router as digital_twin_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for React frontend (http://localhost:5173 / http://127.0.0.1:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register task manager event listener for WebSocket real-time broadcasting
def on_task_event(event: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast(event))
    except Exception:
        pass

task_manager.register_listener(on_task_event)

# Database Startup
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

# Mount API Routers
app.include_router(terminal_router, prefix=settings.API_PREFIX)
app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(files_router, prefix=settings.API_PREFIX)
app.include_router(drives_router, prefix=settings.API_PREFIX)
app.include_router(simulators_router, prefix=settings.API_PREFIX)
app.include_router(digital_twin_router, prefix=settings.API_PREFIX)
app.include_router(system_router, prefix=settings.API_PREFIX)
app.include_router(history_router, prefix=settings.API_PREFIX)
app.include_router(workflows_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)
app.include_router(ws_router)
