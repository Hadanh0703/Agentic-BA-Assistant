import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_ai_ba_workflow_async
from services.project_service import save_message, save_artifact

async def handle_chat(project_id: int, user_input: str, history: str, db, emit):    
    save_message(db, project_id, "user", user_input)
    result = await run_ai_ba_workflow_async(
        user_input=user_input,
        project_id=project_id,
        db=db, 
        history=history,
        emit=emit
    )

    if result["status"] == "need_more_info":
        save_message(db, project_id, "agent", result["feedback"], "Interviewer")
        
    elif result["status"] == "general_response":
        save_message(db, project_id, "agent", result["response"], "Assistant")
        
    elif result["status"] == "awaiting_confirmation":
        story_data = result["user_story"].model_dump() if hasattr(result["user_story"], "model_dump") else result["user_story"]
        save_artifact(db, project_id, "user_story", story_data)     
        save_message(
            db, 
            project_id, 
            "agent", 
            "Tôi đã soạn xong User Story. Vui lòng kiểm tra và xác nhận trên bảng điều khiển!", 
            "Standardizer"
        )

    return result

async def handle_confirm(project_id: int, user_story: dict, db, emit):    
    result = await run_ai_ba_workflow_async(
        user_input=None,
        project_id=project_id,
        db=db, 
        emit=emit,
        confirmed_story=user_story
    )
    return result