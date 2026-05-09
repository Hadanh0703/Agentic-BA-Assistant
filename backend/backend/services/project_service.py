from sqlalchemy.orm import Session
from models import Project, Message, Artifact
from fastapi import HTTPException
import os
import asyncio
from ingest_data import ingest_rag_file

async def handle_ingest_logic(project_id: int, file, ingest_func):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")
    
    os.makedirs("./temp_data", exist_ok=True)
    tmp_path = f"./temp_data/{project_id}_{file.filename}"
    
    try:
        with open(tmp_path, "wb") as f:
            f.write(await file.read())
        
        await asyncio.get_event_loop().run_in_executor(
            None, ingest_func, tmp_path, project_id
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    return f"Đã nạp '{file.filename}' thành công!"

def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    return project


def save_message(db: Session, project_id: int, role: str, content: str, agent_name: str = None):
    msg = Message(project_id=project_id, role=role, content=content, agent_name=agent_name)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def save_artifact(db: Session, project_id: int, artifact_type: str, data, parent_id: int = None):
    artifact = Artifact(
        project_id=project_id, 
        type=artifact_type, 
        data=data,
        parent_id=parent_id, 
        version=1
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def get_messages(db: Session, project_id: int):
    return (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.timestamp.asc()) 
        .all()
    )


def get_artifacts(db: Session, project_id: int):
    return (
        db.query(Artifact)
        .filter(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.asc())
        .all()
    )

def create_new_project(db: Session, name: str):
    p = Project(name=name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def list_all_projects(db: Session):
    return db.query(Project).order_by(Project.created_at.desc()).all()

def delete_project_logic(db: Session, project_id: int):
    p = get_project_or_404(project_id, db)
    db.delete(p)
    db.commit()
    return True