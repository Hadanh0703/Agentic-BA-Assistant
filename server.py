import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base, Project, Message, Artifact
from agents.orchestrator import run_ai_ba_workflow_async
from ingest_data import ingest_rag_file

# ─── DATABASE SETUP ───────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_management.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── LIFESPAN ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("==> Database khởi tạo thành công!")
    yield

# ─── APP INIT ─────────────────────────────────────────────────
app = FastAPI(title="AI-BA Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── WEBSOCKET MANAGER ────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, project_id: str, ws: WebSocket):
        await ws.accept()
        self.active[project_id] = ws

    def disconnect(self, project_id: str):
        self.active.pop(project_id, None)

    async def send(self, project_id: str, data: dict):
        ws = self.active.get(project_id)
        if ws:
            await ws.send_text(json.dumps(data, ensure_ascii=False))

manager = ConnectionManager()

# ─── REQUEST / RESPONSE SCHEMAS ───────────────────────────────
class CreateProjectRequest(BaseModel):
    name: str

class ChatRequest(BaseModel):
    project_id: int
    user_input: str
    history: str = ""

class ConfirmStoryRequest(BaseModel):
    project_id: int
    user_story: dict  # UserStory đã được FE chỉnh sửa (nếu có)

# ─── ENDPOINTS ────────────────────────────────────────────────

@app.post("/projects")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    project = Project(name=req.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "created_at": project.created_at}

@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    db.delete(project)
    db.commit()
    return {"message": "Đã xóa project"}

@app.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    """Nhận PDF từ FE, lưu tạm và nạp vào ChromaDB"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")

    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    await asyncio.get_event_loop().run_in_executor(None, ingest_rag_file, tmp_path)
    os.remove(tmp_path)

    return {"message": f"Đã nạp '{file.filename}' vào ChromaDB thành công!"}

@app.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Chạy pipeline đến bước Standardizer.
    Trả về user_story để FE hiển thị Human-in-the-loop.
    """
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")

    # Lưu message user vào DB
    db.add(Message(
        project_id=req.project_id,
        role="user",
        content=req.user_input
    ))
    db.commit()

    # Gửi trạng thái agent qua WebSocket
    async def emit(step: str, message: str):
        await manager.send(str(req.project_id), {
            "type": "agent_status",
            "step": step,
            "message": message
        })

    result = await run_ai_ba_workflow_async(
        user_input=req.user_input,
        history=req.history,
        emit=emit
    )

    if result["status"] == "need_more_info":
        db.add(Message(
            project_id=req.project_id,
            role="agent",
            content=result["feedback"],
            agent_name="interviewer"
        ))
        db.commit()
        return {"status": "need_more_info", "feedback": result["feedback"]}

    if result["status"] == "error":
        return result

    # Lưu user_story artifact — chờ FE confirm trước khi chạy architect
    user_story = result["user_story"]
    artifact = Artifact(
        project_id=req.project_id,
        type="user_story",
        data=user_story.model_dump()
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return {
        "status": "awaiting_confirmation",
        "artifact_id": artifact.id,
        "user_story": user_story.model_dump()
    }

@app.post("/confirm")
async def confirm_story(req: ConfirmStoryRequest, db: Session = Depends(get_db)):
    """
    Human-in-the-loop: FE xác nhận/chỉnh sửa User Story.
    Sau đó chạy Architect + Risk Observer.
    """
    async def emit(step: str, message: str):
        await manager.send(str(req.project_id), {
            "type": "agent_status",
            "step": step,
            "message": message
        })

    result = await run_ai_ba_workflow_async(
        user_input=None,
        history="",
        emit=emit,
        confirmed_story=req.user_story
    )

    if result["status"] == "error":
        return result

    # Lưu artifacts
    db.add(Artifact(
        project_id=req.project_id,
        type="task_list",
        data=[t.model_dump() for t in result["technical_tasks"]]
    ))
    db.add(Artifact(
        project_id=req.project_id,
        type="risk_report",
        data=result["risk_assessment"].model_dump()
    ))
    db.add(Message(
        project_id=req.project_id,
        role="agent",
        content="Phân rã task hoàn tất.",
        agent_name="orchestrator"
    ))
    db.commit()

    return {
        "status": "success",
        "technical_tasks": [t.model_dump() for t in result["technical_tasks"]],
        "risk_assessment": result["risk_assessment"].model_dump()
    }

@app.get("/projects/{project_id}/artifacts")
def get_artifacts(project_id: int, db: Session = Depends(get_db)):
    artifacts = db.query(Artifact).filter(Artifact.project_id == project_id).all()
    return [{"id": a.id, "type": a.type, "data": a.data, "created_at": a.created_at} for a in artifacts]

@app.get("/projects/{project_id}/messages")
def get_messages(project_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.project_id == project_id).order_by(Message.timestamp).all()
    return [{"role": m.role, "content": m.content, "agent_name": m.agent_name, "timestamp": m.timestamp} for m in messages]

# ─── WEBSOCKET ENDPOINT ───────────────────────────────────────
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(project_id)