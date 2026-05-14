from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Base
from services.websocket_manager import manager
from services.chat_service import handle_chat, handle_confirm
from database import engine, get_db
from middlewares import setup_middlewares
from ingest_data import ingest_rag_file
from schema import CreateProjectRequest, ChatRequest, ConfirmStoryRequest
from services import project_service as svc
from pydantic import BaseModel
from typing import List
from services.jira_service import JiraProvider
from models import UserJiraConfig
from datetime import datetime

class JiraConfigRequest(BaseModel):
    jira_site_url: str
    jira_api_token: str
    jira_project_key: str

class StoryItem(BaseModel):
    story_details: dict
    tasks: List[dict]

class JiraExportRequest(BaseModel):
    stories: List[StoryItem]

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
    owner_id = None
    if req.user_email:
        from models import User
        user = db.query(User).filter(User.email == req.user_email).first()
        if user:
            owner_id = user.id
    return svc.create_new_project(db, req.name, owner_id=owner_id)

@app.get("/projects")
def list_projects(user_email: str = None, db: Session = Depends(get_db)):
    if user_email:
        from models import User, Project
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return []
        projects = db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()
        return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]
    return svc.list_all_projects(db)

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    svc.delete_project_logic(db, project_id)
    return {"message": "Đã xóa project"}

@app.get("/projects/{project_id}/messages")
def project_messages(project_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db) 
    return svc.get_messages(db, project_id) 

@app.get("/projects/{project_id}/files")
def list_project_files(project_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db)
    return svc.get_project_files(db, project_id)

@app.get("/projects/{project_id}/artifacts")
def project_artifacts(project_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db) 
    return svc.get_artifacts(db, project_id)

@app.post("/ingest/{project_id}")
async def ingest_pdf(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db)    
    message = await svc.handle_ingest_logic(project_id, file, ingest_rag_file, db)  
    return {"message": message}

@app.put("/artifacts/{artifact_id}")
async def update_artifact(artifact_id: int, req_data: dict, db: Session = Depends(get_db)):
    updated_artifact = svc.update_artifact_data(db, artifact_id, req_data)
    return updated_artifact

@app.delete("/projects/{project_id}/artifacts/{artifact_id}")
async def delete_artifact(project_id: int, artifact_id: int, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db)
    success = svc.delete_artifact_logic(db, project_id, artifact_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng task này")
        
    return {"status": "success", "message": "Đã xóa bảng task thành công"}

@app.delete("/projects/{project_id}/files/{file_name}")
async def delete_knowledge_file(project_id: int, file_name: str, db: Session = Depends(get_db)):
    svc.get_project_or_404(project_id, db)
    message = await svc.delete_file_logic(project_id, file_name, db)
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


@app.post("/api/jira/export")
async def export_jira_endpoint(req: JiraExportRequest):
    jira = JiraProvider()

    if not jira.url or not jira.project_key:
        raise HTTPException(
            status_code=400,
            detail="Thiếu cấu hình Jira trong .env"
        )

    sp_field_id = jira.get_story_points_field()
    print(f"SP Field ID: {sp_field_id}")

    board_id = jira.get_board_id(jira.project_key)
    if not board_id:
        print("Không tìm thấy board — task sẽ vào Backlog")

    exported_keys = []

    for item in req.stories:
        sd = item.story_details
        tsks = item.tasks

        story_title = sd.get('title', 'Untitled')
        summary = f"[Story] {story_title}"
        ac_text = "\n".join([f"- {ac}" for ac in sd.get('acceptance_criteria', [])])
        description = (
            f"Role: {sd.get('role')}\n"
            f"Action: {sd.get('action')}\n"
            f"Benefit: {sd.get('benefit')}\n\n"
            f"Acceptance Criteria:\n{ac_text}"
        )

        print(f"\nĐang tạo Story: {summary}")
        res_story = jira.create_issue(summary, description, issue_type="Story")

        if not res_story or 'key' not in res_story:
            print(f" Bỏ qua story '{story_title}' do lỗi tạo issue")
            continue

        parent_key = res_story['key']
        exported_keys.append(parent_key)
        story_issue_keys = [parent_key]

        total_sp = sum(t.get('story_point', 0) or 0 for t in tsks)
        if total_sp and sp_field_id:
            jira.update_story_points(parent_key, sp_field_id, total_sp)
            print(f" Story {parent_key} tổng SP: {total_sp}")

        for t in tsks:
            t_summary = f"[{t.get('type', 'Task')}] {t.get('title', 'Untitled')}"
            t_desc = (
                f"{t.get('description', '')}\n\n"
                f"Parent Story: {parent_key}\n"
                f"Priority: {t.get('priority', '?')}"
            )
            sp = t.get('story_point')

            print(f"  Đang tạo Task: {t_summary}")
            res_task = jira.create_issue(t_summary, t_desc, issue_type="Task")

            if res_task and 'key' in res_task:
                task_key = res_task['key']
                story_issue_keys.append(task_key)

                if sp and sp_field_id:
                    jira.update_story_points(task_key, sp_field_id, sp)

        if board_id and story_issue_keys:
            sprint_name = f"{story_title[:50]}"  # Giới hạn 50 ký tự
            sprint_id = jira.create_sprint(board_id, sprint_name)
            if sprint_id:
                jira.move_to_sprint(sprint_id, story_issue_keys)
                print(f"  Moved {len(story_issue_keys)} issues vào sprint '{sprint_name}'")
            else:
                print(f"  Không tạo được sprint cho '{story_title}'")

    return {"status": "success", "exported_stories": exported_keys}


@app.post("/users/{email}/jira-config")
def save_jira_config(email: str, req: JiraConfigRequest, db: Session = Depends(get_db)):
    config = db.query(UserJiraConfig).filter(UserJiraConfig.user_email == email).first()
    if config:
        # Update nếu đã có
        config.jira_site_url = req.jira_site_url
        config.jira_api_token = req.jira_api_token
        config.jira_project_key = req.jira_project_key
        config.updated_at = datetime.utcnow()
    else:
        # Tạo mới
        config = UserJiraConfig(
            user_email=email,
            jira_site_url=req.jira_site_url,
            jira_api_token=req.jira_api_token,
            jira_project_key=req.jira_project_key,
        )
        db.add(config)
    db.commit()
    return {"message": "Đã lưu Jira config thành công!"}

@app.get("/users/{email}/jira-config")
def get_jira_config(email: str, db: Session = Depends(get_db)):
    config = db.query(UserJiraConfig).filter(UserJiraConfig.user_email == email).first()
    if not config:
        raise HTTPException(status_code=404, detail="Chưa có Jira config")
    return {
        "jira_site_url": config.jira_site_url,
        "jira_project_key": config.jira_project_key,
    }


class UpsertUserRequest(BaseModel):
    email: str
    name: str = None
    avatar: str = None

@app.post("/users/me/upsert")
def upsert_user(req: UpsertUserRequest, db: Session = Depends(get_db)):
    from models import User
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email, name=req.name, avatar=req.avatar)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}