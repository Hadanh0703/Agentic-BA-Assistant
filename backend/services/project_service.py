from sqlalchemy.orm import Session
from models import Project, Message, Artifact, KnowledgeFile 
from fastapi import HTTPException
import models
import os
import asyncio
from ingest_data import ingest_rag_file, delete_rag_file 


def create_new_project(db: Session, name: str):
    p = Project(name=name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def list_all_projects(db: Session):
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project không tồn tại")
    return project

def delete_project_logic(db: Session, project_id: int):
    p = get_project_or_404(project_id, db)
    db.query(KnowledgeFile).filter(KnowledgeFile.project_id == project_id).delete()
    db.delete(p)
    db.commit()
    return True

def get_messages(db: Session, project_id: int):
    return (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.timestamp.asc()) 
        .all()
    )

def get_project_files(db: Session, project_id: int):
    return (
        db.query(KnowledgeFile)
        .filter(KnowledgeFile.project_id == project_id)
        .all()
    )

def get_artifacts(db: Session, project_id: int):
    return (
        db.query(Artifact)
        .filter(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.asc())
        .all()
    )


async def handle_ingest_logic(project_id: int, file, ingest_func, db: Session):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")
    
    os.makedirs("./temp_data", exist_ok=True)
    file_path = f"./temp_data/{project_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, ingest_func, file_path, project_id
        )

        existing_file = db.query(KnowledgeFile).filter(
            KnowledgeFile.project_id == project_id, 
            KnowledgeFile.file_name == file.filename
        ).first()

        if not existing_file:
            db_file = KnowledgeFile(project_id=project_id, file_name=file.filename)
            db.add(db_file)
            db.commit()

        return f"Đã nạp '{file.filename}' thành công!"
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

async def delete_file_logic(project_id: int, file_name: str, db: Session):
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, delete_rag_file, file_name, project_id
        )

        db_file = db.query(KnowledgeFile).filter(
            KnowledgeFile.project_id == project_id, 
            KnowledgeFile.file_name == file_name
        ).first()
        
        if db_file:
            db.delete(db_file)
            db.commit()

        return f"Hệ thống đã quên kiến thức từ file '{file_name}'"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa file: {str(e)}")
    

def update_artifact_data(db: Session, artifact_id: int, new_data: dict):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng Task này")
    current_data = dict(artifact.data) if artifact.data else {}
    current_data.update(new_data)
    artifact.data = current_data
    
    db.commit()
    db.refresh(artifact)
    return artifact


def delete_artifact_logic(db: Session, project_id: int, artifact_id: int):
    artifact = db.query(models.Artifact).filter(
        models.Artifact.id == artifact_id, 
        models.Artifact.project_id == project_id
    ).first()
    
    if not artifact:
        return None  
        
    db.delete(artifact)
    db.commit()
    return True



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


