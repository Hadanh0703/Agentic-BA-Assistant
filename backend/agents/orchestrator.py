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

# ── INTENT SCHEMA ─────────────────────────────────────────────
class IntentResult(BaseModel):
    intent: str = Field(description="'general', 'rag_qa' hoặc 'feature_request'")
    reason: str = Field(description="Lý do phân loại ngắn gọn")

async def classify_intent(user_input: str, history: str = "") -> str:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    structured_llm = llm.with_structured_output(IntentResult)
    messages = [
        # HIỆU CHỈNH PROMPT: Thêm luật nhận diện câu trả lời làm rõ nghiệp vụ
        SystemMessage(content=(
            "Phân loại ý định người dùng thành ĐÚNG 1 trong 3 loại dựa trên ngữ cảnh hội thoại:\n\n"
            
            "- 'feature_request': Người dùng muốn XÂY DỰNG/YÊU CẦU tính năng mới HOẶC họ đang TRẢ LỜI, CUNG CẤP THÊM THÔNG TIN cho câu hỏi làm rõ nghiệp vụ trước đó của hệ thống.\n"
            "  DẤU HIỆU: Bắt đầu bằng 'tôi muốn', 'tôi cần', 'xây dựng', 'làm tính năng', 'phát triển' HOẶC là nội dung bổ sung ngữ cảnh cho một tính năng đang bàn dở trong lịch sử chat.\n"
            "  QUY TẮC QUAN TRỌNG: Kể cả khi input ngắn và không có từ khóa hành động, nếu trong lịch sử hệ thống đang hỏi làm rõ một tính năng và người dùng nhập câu trả lời cho câu hỏi đó, hãy LUÔN phân loại là 'feature_request'.\n\n"
            
            "- 'rag_qa': Người dùng đang HỎI hoặc TRA CỨU thông tin thuần túy từ tài liệu.\n"
            "  DẤU HIỆU: Câu hỏi muốn biết thông tin quy định, không có ý định xây dựng hay trả lời làm rõ tính năng.\n"
            "  Ví dụ: 'Chính sách hủy sân là gì?', 'Hạng Vàng có ưu đãi gì?' → rag_qa\n\n"
            
            "- 'general': Chào hỏi, hỏi kiến thức chung không liên quan tài liệu dự án hoặc chuyển sang chủ đề xã giao khác.\n"
            "  Ví dụ: 'Chào bạn', 'RAG là gì?' → general"
        )),
        HumanMessage(content=f"Lịch sử chat trước đó:\n{history}\n\nCâu nhập mới nhất của người dùng: {user_input}")
    ]
    result = await structured_llm.ainvoke(messages)
    return result.intent

async def handle_general_chat(user_input: str) -> str:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.5,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        SystemMessage(content="Bạn là AI-BA Assistant thân thiện. Trả lời ngắn gọn bằng tiếng Việt."),
        HumanMessage(content=user_input)
    ]
    response = await llm.ainvoke(messages)
    return response.content

async def handle_rag_qa(user_input: str, context: str) -> str:
    """Chuyên trách xử lý câu hỏi tra cứu tài liệu — strict, không hallucinate."""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        SystemMessage(content=(
            "Bạn là trợ lý AI-BA chuyên nghiệp. Trả lời câu hỏi DỰA TRÊN NGỮ CẢNH ĐƯỢC CUNG CẤP.\n"
            "QUY TẮC:\n"
            "1. Chỉ dùng thông tin trong ngữ cảnh. Không suy đoán, không bịa đặt.\n"
            "2. Nếu không có thông tin → trả lời: 'Tôi không tìm thấy thông tin này trong tài liệu dự án.'\n"
            "3. Trả lời ngắn gọn, trực tiếp bằng tiếng Việt."
        )),
        HumanMessage(content=f"Ngữ cảnh:\n{context}\n\nCâu hỏi: {user_input}")
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
            return {"status": "error", "step": "architect", "detail": str(e)}

        await log("risk_observer", "Đang kiểm tra rủi ro & chất lượng...")
        max_retries = 2
        final_quality_report = None

        for attempt in range(max_retries + 1):
            try:
                quality_report = await call_risk_observer_async(tasks_obj)
            except Exception as e:
                return {"status": "error", "step": "risk_observer", "detail": str(e)}

            final_quality_report = quality_report

            if quality_report.is_safe:
                await log("risk_observer", f"✅ Đạt chuẩn (sau {attempt} lần kiểm tra).")
                break
            else:
                if attempt < max_retries:
                    flags = ", ".join(quality_report.red_flags)
                    await log("architect", f"⚠️ Lần {attempt + 1}: Phát hiện rủi ro → Đang sửa lại...")
                    try:
                        tasks_obj = await call_architect_async(
                            user_story_obj,
                            project_id=project_id,
                            feedback=quality_report.recommendations
                        )
                    except Exception as e:
                        return {"status": "error", "step": "architect_retry", "detail": str(e)}
                else:
                    await log("risk_observer", "⚠️ Đã đạt giới hạn retry.")

        return {
            "status": "success",
            "user_story": user_story_obj.model_dump(),
            "tasks": [t.model_dump() for t in tasks_obj.tasks],
            "risk_report": final_quality_report.model_dump()
        }

    confirms = ["đúng", "ok", "chuẩn", "xác nhận", "đồng ý", "chốt", "oke", "hợp lý"]
    clean_input = user_input.lower().strip().replace(".", "") if user_input else ""
    is_confirm = any(word in clean_input for word in confirms)

    feature_keywords = ["tôi muốn", "tôi cần", "xây dựng", "làm tính năng", 
                        "phát triển", "tạo tính năng", "implement", "thiết kế tính năng"]
    is_feature_request = any(kw in clean_input for kw in feature_keywords)

    if is_confirm or is_feature_request:
        intent = "feature_request"
        print(f"[debug] intent=feature_request (keyword match: is_confirm={is_confirm}, is_feature={is_feature_request})")
    else:
        intent = await classify_intent(user_input, history)
        print(f"[debug] intent={intent} (LLM classified)")

    # ── MODE: GENERAL CHAT ────────────────────────────────────────
    if intent == "general":
        await log("assistant", "Đang trả lời câu hỏi chung...")
        response = await handle_general_chat(user_input)
        return {"status": "general_response", "response": response}


    if intent == "rag_qa":
        await log("assistant", "Đang tra cứu tài liệu dự án...")
        context_rag = await asyncio.to_thread(query_rag, user_input, project_id)
        if context_rag and len(context_rag) > 50:
            response = await handle_rag_qa(user_input, context_rag)
        else:
            response = "Tôi không tìm thấy thông tin này trong tài liệu dự án."
        return {"status": "general_response", "response": response}

    print("[debug] Bắt đầu query RAG cho feature pipeline...")
    context_rag = await asyncio.to_thread(query_rag, user_input, project_id)
    print(f"[debug] RAG context length={len(context_rag) if context_rag else 0}")

    await log("interviewer", "Đang phân tích và làm rõ yêu cầu...")
    try:
        interview_result = await call_interviewer_async(user_input, history, context_rag=context_rag)
        print(f"[debug] interviewer: is_sufficient={interview_result.is_sufficient}")
    except Exception as e:
        return {"status": "error", "step": "interviewer", "detail": str(e)}

    if not interview_result.is_sufficient:
        return {
            "status": "general_response",
            "response": interview_result.feedback
        }

    await log("standardizer", "Đang soạn thảo User Story chuẩn Agile...")
    try:
        user_story_obj = await call_standardizer_async(interview_result.clarified_requirement)
        print(f"[debug] standardizer: action='{user_story_obj.action[:50]}'")
    except Exception as e:
        return {"status": "error", "step": "standardizer", "detail": str(e)}

    return {"status": "awaiting_confirmation", "user_story": user_story_obj}