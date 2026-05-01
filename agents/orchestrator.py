import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import TaskList
from agents.interviewer import call_interviewer
from agents.standardizer import call_standardizer
from agents.architect import call_architect
from agents.risk_observer import call_risk_observer
from dotenv import load_dotenv

load_dotenv()

def run_ai_ba_workflow(user_input, history=""):
    print("\n" + "="*50)
    print("BẮT ĐẦU QUY TRÌNH AI-BA ASSISTANT")
    print("="*50)

    print("\n[Step 1] Đang phân tích và làm rõ yêu cầu...")
    try:
        interview_result = call_interviewer(user_input, history)
    except Exception as e:
        return {"status": "error", "step": "interviewer", "detail": str(e)}

    if not interview_result.is_sufficient:
        print("Chưa đủ thông tin.")
        return {"status": "need_more_info", "feedback": interview_result.feedback}

    print("Yêu cầu đã rõ ràng.")
    req_summary = interview_result.clarified_requirement

    print("\n[Step 2] Đang soạn thảo User Story chuẩn Agile...")
    try:
        user_story_obj = call_standardizer(req_summary)
    except Exception as e:
        return {"status": "error", "step": "standardizer", "detail": str(e)}
    print(f" USER STORY : As a {user_story_obj.role}, I want to {user_story_obj.action} SO THAT {user_story_obj.benefit}")
    print(f" Tiêu chí chấp nhận (AC): {user_story_obj.acceptance_criteria}")
    
    print("\n[Step 3] Kiến trúc sư đang phân rã Technical Tasks (RAG)...")
    try:
        tasks_obj = call_architect(user_story_obj)
    except Exception as e:
        return {"status": "error", "step": "architect", "detail": str(e)}

    print("\n[Step 4] Đang kiểm tra rủi ro và chất lượng task...")
    max_retries = 2
    final_quality_report = None

    for attempt in range(max_retries + 1):
        try:
            quality_report = call_risk_observer(tasks_obj)
        except Exception as e:
            return {"status": "error", "step": "risk_observer", "detail": str(e)}

        final_quality_report = quality_report

        if quality_report.is_safe:
            print(f"Kết quả đạt chuẩn an toàn (Sau {attempt} lần sửa).")
            break
        else:
            if attempt < max_retries:
                print(f" Lần {attempt + 1}: Phát hiện rủi ro. Đang gửi feedback yêu cầu sửa lại...")
                print(f" Lý do: {', '.join(quality_report.red_flags)}")
                try:
                    tasks_obj = call_architect(user_story_obj, feedback=quality_report.recommendations)
                except Exception as e:
                    return {"status": "error", "step": "architect_retry", "detail": str(e)}
            else:
                print(" Đã đạt giới hạn sửa lỗi. Kết thúc với cảnh báo còn tồn tại.")

    print("\n" + "="*50)
    print(" QUY TRÌNH HOÀN TẤT")
    print("="*50)

    return {
        "status": "success",
        "user_story": user_story_obj,
        "technical_tasks": tasks_obj.tasks,
        "risk_assessment": final_quality_report
    }