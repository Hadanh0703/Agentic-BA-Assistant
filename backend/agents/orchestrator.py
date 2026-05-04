import sys
import os
import asyncio
from typing import Callable, Awaitable, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models  
from agents.interviewer import call_interviewer_async
from agents.standardizer import call_standardizer_async
from agents.architect import call_architect_async
from agents.risk_observer import call_risk_observer_async
from ingest_data import query_rag 
from schema import UserStory  
from dotenv import load_dotenv

load_dotenv()

# ─── INTENT CLASSIFIER ────────────────────────────────────────
class IntentResult(BaseModel):
    intent: str = Field(description="'general' hoặc 'business'")
    reason: str = Field(description="Lý do phân loại ngắn gọn")

async def classify_intent(user_input: str) -> str:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    structured_llm = llm.with_structured_output(IntentResult)
    messages = [
        SystemMessage(content=(
            "Phân loại ý định của người dùng thành 1 trong 2 loại:\n"
            "- 'general': Chào hỏi, hỏi kiến thức chung.\n"
            "- 'business': Yêu cầu tính năng, mô tả nghiệp vụ, phân tích hệ thống."
        )),
        HumanMessage(content=user_input)
    ]
    result = await structured_llm.ainvoke(messages)
    return result.intent

async def handle_general_chat(user_input: str) -> str:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        SystemMessage(content="Bạn là AI-BA Assistant thân thiện, trả lời ngắn gọn."),
        HumanMessage(content=user_input)
    ]
    response = await llm.ainvoke(messages)
    return response.content

# ─── MAIN WORKFLOW ────────────────────────────────────────────
async def run_ai_ba_workflow_async(
    user_input: Optional[str],
    project_id: int,
    db: Session,
    history: str = "",
    emit: Callable[[str, str], Awaitable[None]] = None,
    confirmed_story: Optional[dict] = None
):
    async def log(step: str, msg: str):
        if emit: await emit(step, msg)

    if confirmed_story is not None:
        if "title" not in confirmed_story or not confirmed_story["title"]:
            confirmed_story["title"] = f"Story: {confirmed_story.get('action', 'Nghiệp vụ hệ thống')[:30]}"
        
        user_story_obj = UserStory(**confirmed_story)
        parent_story = db.query(models.Artifact).filter(
            models.Artifact.project_id == project_id,
            models.Artifact.type == "user_story"
        ).order_by(models.Artifact.id.desc()).first()

        await log("architect", "Kiến trúc sư đang phân rã Technical Tasks (RAG)...")
        try:
            tasks_obj = await call_architect_async(user_story_obj, project_id=project_id)
        except Exception as e:
            return {"status": "error", "step": "architect", "detail": str(e)}

        await log("risk_observer", "Đang kiểm tra rủi ro...")
        try:
            final_quality_report = await call_risk_observer_async(tasks_obj)
        except Exception as e:
            return {"status": "error", "step": "risk_observer", "detail": str(e)}

        new_tasks_artifact = models.Artifact(
            project_id=project_id,
            type="task_list",
            parent_id=parent_story.id if parent_story else None,
            data={
                "story_title": user_story_obj.title,
                "tasks": [task.dict() for task in tasks_obj.tasks]
            }
        )
        db.add(new_tasks_artifact)

        new_risk_artifact = models.Artifact(
            project_id=project_id,
            type="risk_report",
            parent_id=parent_story.id if parent_story else None,
            data=final_quality_report.dict()
        )
        db.add(new_risk_artifact)       
        db.commit() 

        return {
            "status": "success",
            "technical_tasks": tasks_obj.tasks,
            "risk_assessment": final_quality_report
        }

    # ── PHÂN LOẠI Ý ĐỊNH ───────────
    confirms = ["đúng", "ok", "chuẩn", "xác nhận", "đồng ý", "chốt"]
    clean_input = user_input.lower().strip().replace(".", "") if user_input else ""
    is_confirm = clean_input in confirms
    
    intent = "business" if is_confirm else await classify_intent(user_input)

    # ── MODE: GENERAL CHAT ────────────────────────────────────
    if intent == "general":
        response = await handle_general_chat(user_input)
        return {"status": "general_response", "response": response}

    # ── MODE: BUSINESS PIPELINE ───────────────────────────────
    context_rag = await asyncio.to_thread(query_rag, user_input, project_id)
    await log("interviewer", "Đang phân tích yêu cầu...")
    interview_result = await call_interviewer_async(user_input, history, context_rag=context_rag)

    if not interview_result.is_sufficient:
        return {
            "status": "need_more_info", 
            "feedback": interview_result.feedback,
            "response_type": interview_result.response_type
        }
    await log("standardizer", "Đang soạn thảo User Story...")
    user_story_obj = await call_standardizer_async(interview_result.clarified_requirement)

    return {"status": "awaiting_confirmation", "user_story": user_story_obj}