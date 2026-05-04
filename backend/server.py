from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from sqlalchemy.orm import Session
from models import Base
from services.websocket_manager import manager
from services.chat_service import handle_chat, handle_confirm
from database import engine, get_db
from middlewares import setup_middlewares
from ingest_data import ingest_rag_file
from schema import CreateProjectRequest, ChatRequest, ConfirmStoryRequest
from services import project_service as svc

# ─── APP ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("==> Database sẵn sàng!")
    yield

app = FastAPI(title="AI-BA Assistant API", lifespan=lifespan)
# ─── MIDDLEWARE ──────────────────────────────────────────────────────

setup_middlewares(app)

# ─── PROJECT ──────────────────────────────────────────────────────

@app.post("/projects")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    return svc.create_new_project(db, req.name)

@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return svc.list_all_projects(db)

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    svc.delete_project_logic(db, project_id)
    return {"message": "Đã xóa project"}

@app.get("/projects/{project_id}/messages")
def project_messages(project_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db) 
    return svc.get_messages(db, project_id) 

@app.get("/projects/{project_id}/artifacts")
def project_artifacts(project_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db) 
    return svc.get_artifacts(db, project_id)

@app.post("/ingest/{project_id}")
async def ingest_pdf(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db)    
    message = await svc.handle_ingest_logic(project_id, file, ingest_rag_file)  
    return {"message": message}


# ─── CHAT ─────────────────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    svc.get_project_or_404(req.project_id, db)
    async def emit(step: str, message: str):
        await manager.send(
            str(req.project_id),
            {"type": "agent_status", "step": step, "message": message}
        )
    return await handle_chat(req.project_id, req.user_input, req.history, db, emit)

@app.post("/confirm")
async def confirm(req: ConfirmStoryRequest, db: Session = Depends(get_db)):
    svc.get_project_or_404(req.project_id, db)
    async def emit(step: str, message: str):
        await manager.send(
            str(req.project_id),
            {"type": "agent_status", "step": step, "message": message}
        )
    return await handle_confirm(req.project_id, req.user_story, db, emit)

# ─── WEBSOCKET ────────────────────────────────────────────────
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project_id)