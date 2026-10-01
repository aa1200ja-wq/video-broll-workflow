from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.projects import router as projects_router
from app.routes.system import router as system_router

app = FastAPI(title="B-roll Workflow", version="1.0.0")
app.include_router(projects_router)
app.include_router(system_router)

WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
