import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_ai_ba_workflow_async
from services.project_service import save_message, save_artifact, get_messages

async def handle_chat(project_id: int, user_input: str, history: str, db, emit):    
    save_message(db, project_id, "user", user_input)
    
    db_messages = get_messages(db, project_id)
    
    past_messages = db_messages[:-1] if len(db_messages) > 1 else []
    
    history_parts = []
    for msg in past_messages[-10:]:
        sender_type = getattr(msg, "sender_type", "user")
        role = "Assistant" if sender_type == "agent" or getattr(msg, "role", "user") == "agent" else "User"
        content = getattr(msg, "content", "")
        history_parts.append(f"{role}: {content}")
        
    auto_history = "\n".join(history_parts)

    result = await run_ai_ba_workflow_async(
        user_input=user_input,
        project_id=project_id,
        db=db, 
        history=auto_history, 
        emit=emit
    )

    if result["status"] == "general_response":
        is_clarifying = any(word in result["response"].lower() for word in ["hỏi thêm", "làm rõ", "quy định", "chính sách", "liệu", "không?"])
        sender_name = "Interviewer" if is_clarifying else "Assistant"
        
        save_message(db, project_id, "agent", result["response"], sender_name)
        
    elif result["status"] == "awaiting_confirmation":
        story_data = result["user_story"].model_dump() if hasattr(result["user_story"], "model_dump") else result["user_story"]
        
        # ── SỬA LỖI 1: Ép kiểu Object lồng về dict thuần trước khi return để FastAPI serialize được sang JSON ──
        result["user_story"] = story_data
        
        save_artifact(db, project_id, "user_story", story_data)     
        save_message(
            db, 
            project_id, 
            "agent", 
            "Tôi đã soạn xong User Story. Vui lòng kiểm tra, chỉnh sửa (nếu cần) và xác nhận trên bảng điều khiển!", 
            "Standardizer"
        )

    # ── SỬA LỖI 2: Bắt trạng thái lỗi ngầm từ Agent để đẩy text lên giao diện thay vì im lặng hoàn toàn ──
    elif result["status"] == "error":
        error_msg = f"Hệ thống gặp lỗi tại [{result['step']}]: {result['detail']}"
        save_message(db, project_id, "agent", error_msg, "System")
        return {
            "status": "general_response",
            "response": error_msg
        }

    return result

async def handle_confirm(project_id: int, user_story: dict, db, emit):    
    result = await run_ai_ba_workflow_async(
        user_input=None,
        project_id=project_id,
        db=db, 
        emit=emit,
        confirmed_story=user_story
    )
    
    if result.get("status") == "success":
        tasks = result.get("tasks", [])
        risk_report = result.get("risk_report")

        combined_data = {
            "story_details": user_story.model_dump() if hasattr(user_story, 'model_dump') else user_story,
            "tasks": [task.model_dump() if hasattr(task, 'model_dump') else task for task in tasks],
            "risk_report": risk_report.model_dump() if hasattr(risk_report, 'model_dump') else risk_report
        }
        
        save_artifact(db, project_id, "task_list", combined_data)  
        story_title = combined_data["story_details"].get('title', 'Mới')
        
        save_message(
            db, 
            project_id, 
            "agent", 
            f"Đã hoàn thành phân rã Task cho Story: {story_title}. Bạn có thể xem định dạng User Story chuẩn và danh sách Task chi tiết trong Workspace.", 
            "Architect"
        )

    return result