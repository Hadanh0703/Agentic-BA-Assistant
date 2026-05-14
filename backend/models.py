from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="projects")

    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    knowledge_files = relationship("KnowledgeFile", back_populates="project", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(String(50), nullable=False) 
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="messages")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  
    type = Column(String(50), nullable=False) 
    parent_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    version = Column(Integer, default=1) 
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="artifacts")
    children = relationship("Artifact", backref="parent", remote_side=[id])


class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_name = Column(String(255), nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="knowledge_files")

class UserJiraConfig(Base):
    __tablename__ = "user_jira_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), unique=True, nullable=False)
    jira_site_url = Column(String(255), nullable=False)
    jira_api_token = Column(String(500), nullable=False)
    jira_project_key = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    avatar = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")