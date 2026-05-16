import sys
import os
import asyncio
from typing import Callable, Awaitable, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.interviewer import call_interviewer_async
from agents.standardizer import call_standardizer_async
from agents.architect import call_architect_async
from agents.risk_observer import call_risk_observer_async
from ingest_data import query_rag
from schema import UserStory
from dotenv import load_dotenv

load_dotenv()

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
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.5,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        SystemMessage(content="Bạn là AI-BA Assistant thân thiện. Trả lời bằng tiếng Việt."),
        HumanMessage(content=user_input)
    ]
    response = await llm.ainvoke(messages)
    return response.content

async def handle_rag_qa(user_input: str, context: str) -> str:
    """
    Hàm chuyên trách xử lý câu hỏi tra cứu tài liệu (RAG).
    Đặt temperature = 0 và cấu hình System Prompt nghiêm ngặt để chống ảo tưởng thông tin.
    """
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        SystemMessage(content=(
            "Bạn là một trợ lý AI-BA chuyên nghiệp. Nhiệm vụ của bạn là trả lời câu hỏi của người dùng "
            "DỰA TRÊN NGỮ CẢNH (CONTEXT) ĐƯỢC CUNG CẤP.\n"
            "QUY TẮC NGHIÊM NGẶT:\n"
            "1. Chỉ sử dụng thông tin có trong ngữ cảnh. Không tự ý suy đoán, không bịa đặt, không thêm thắt thông tin bên ngoài.\n"
            "2. Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy phản hồi chính xác là: 'Tôi không tìm thấy thông tin này trong tài liệu dự án.'\n"
            "3. Trả lời ngắn gọn, trực tiếp, tập trung vào câu hỏi bằng tiếng Việt."
        )),
        HumanMessage(content=f"Ngữ cảnh tài liệu dự án:\n{context}\n\nCâu hỏi của người dùng: {user_input}")
    ]
    response = await llm.ainvoke(messages)
    return response.content

async def run_ai_ba_workflow_async(
    user_input: Optional[str],
    project_id: int,
    db: Session,
    history: str = "",
    emit: Callable[[str, str], Awaitable[None]] = None,
    confirmed_story: Optional[Union[dict, UserStory]] = None
):
    async def log(step: str, msg: str):
        print(f"[{step}] {msg}")
        if emit:
            await emit(step, msg)

    # ── MODE: ARCHITECT + SELF-CORRECTION ────────────────────────
    if confirmed_story is not None:
        if isinstance(confirmed_story, dict):
            user_story_obj = UserStory(**confirmed_story)
        else:
            user_story_obj = confirmed_story

        if not user_story_obj.title:
            user_story_obj.title = f"Story: {user_story_obj.action[:30]}"

        await log("architect", "Kiến trúc sư đang phân rã Technical Tasks (RAG)...")
        try:
            tasks_obj = await call_architect_async(user_story_obj, project_id=project_id)
        except Exception as e:
            print(f"[architect] LỖI: {repr(e)}")
            return {"status": "error", "step": "architect", "detail": str(e)}

        await log("risk_observer", "Đang kiểm tra rủi ro & chất lượng...")
        max_retries = 2
        final_quality_report = None

        for attempt in range(max_retries + 1):
            try:
                quality_report = await call_risk_observer_async(tasks_obj)
            except Exception as e:
                print(f"[risk_observer] LỖI: {repr(e)}")
                return {"status": "error", "step": "risk_observer", "detail": str(e)}

            final_quality_report = quality_report

            if quality_report.is_safe:
                await log("risk_observer", f"✅ Đạt chuẩn an toàn (sau {attempt} lần kiểm tra).")
                break
            else:
                if attempt < max_retries:
                    flags = ", ".join(quality_report.red_flags)
                    await log("architect", f"⚠️ Lần {attempt + 1}: Phát hiện rủi ro → Đang sửa lại...")
                    print(f"[architect] Lý do: {flags}")
                    try:
                        tasks_obj = await call_architect_async(
                            user_story_obj,
                            project_id=project_id,
                            feedback=quality_report.recommendations
                        )
                    except Exception as e:
                        print(f"[architect_retry] LỖI: {repr(e)}")
                        return {"status": "error", "step": "architect_retry", "detail": str(e)}
                else:
                    await log("risk_observer", "⚠️ Đã đạt giới hạn retry. Kết thúc với cảnh báo.")

        return {
            "status": "success",
            "user_story": user_story_obj.model_dump(),
            "tasks": [t.model_dump() for t in tasks_obj.tasks],
            "risk_report": final_quality_report.model_dump()
        }

    # ── MODE: INTENT CLASSIFICATION ──────────────────────────────
    confirms = ["đúng", "ok", "chuẩn", "xác nhận", "đồng ý", "chốt", "oke", "hợp lý"]
    clean_input = user_input.lower().strip().replace(".", "") if user_input else ""
    is_confirm = any(word in clean_input for word in confirms)

    print(f"[debug] is_confirm={is_confirm}, input='{user_input[:40]}...'")

    intent = "business" if is_confirm else await classify_intent(user_input)
    print(f"[debug] intent={intent}")

    # ── MODE: GENERAL CHAT ────────────────────────────────────────
    if intent == "general":
        await log("assistant", "Đang trả lời câu hỏi chung...")
        response = await handle_general_chat(user_input)
        return {"status": "general_response", "response": response}

    # ── MODE: BUSINESS PIPELINE ───────────────────────────────────
    print("[debug] Bắt đầu query RAG...")
    context_rag = await asyncio.to_thread(query_rag, user_input, project_id)
    print(f"[debug] RAG done, length={len(context_rag) if context_rag else 0}")

    # Mở rộng từ khóa nhận diện câu hỏi tra cứu thông tin để bắt trúng luồng RAG tốt hơn
    is_question = any(word in user_input.lower() for word in ["?", "là gì", "như thế nào", "giải thích", "bao nhiêu", "không", "mấy", "quy định"])

    if is_question and context_rag and len(context_rag) > 50:
        print("[debug] Trả lời từ RAG context thông qua handle_rag_qa...")
        # Đổi sang gọi hàm chuyên dụng với temperature=0 và prompt chặt chẽ
        response = await handle_rag_qa(user_input, context_rag)
        return {"status": "general_response", "response": response}

    await log("interviewer", "Đang phân tích và làm rõ yêu cầu...")
    try:
        print("[debug] Bắt đầu gọi interviewer LLM...")
        interview_result = await call_interviewer_async(user_input, history, context_rag=context_rag)
        print(f"[debug] interviewer xong: is_sufficient={interview_result.is_sufficient}")
        print(f"[debug] response_type={interview_result.response_type}")
    except Exception as e:
        print(f"[interviewer] LỖI: {repr(e)}")
        return {"status": "error", "step": "interviewer", "detail": str(e)}

    if not interview_result.is_sufficient:
        print(f"[debug] Hỏi thêm: {interview_result.feedback[:60]}...")
        return {
            "status": "need_more_info",
            "feedback": interview_result.feedback,
            "response_type": interview_result.response_type
        }

    await log("standardizer", "Đang soạn thảo User Story chuẩn Agile...")
    try:
        print("[debug] Bắt đầu gọi standardizer LLM...")
        user_story_obj = await call_standardizer_async(interview_result.clarified_requirement)
        print(f"[debug] standardizer xong: action='{user_story_obj.action[:50]}'")
    except Exception as e:
        print(f"[standardizer] LỖI: {repr(e)}")
        return {"status": "error", "step": "standardizer", "detail": str(e)}

    return {"status": "awaiting_confirmation", "user_story": user_story_obj}