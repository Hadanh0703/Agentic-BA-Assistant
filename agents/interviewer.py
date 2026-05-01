import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import List, Optional

# Load biến môi trường
load_dotenv()

class InterviewResponse(BaseModel):
    is_sufficient: bool = Field(description="True nếu yêu cầu đã đủ thông tin, False nếu cần hỏi thêm")
    feedback: str = Field(description="Câu hỏi gợi mở nếu thiếu, hoặc lời xác nhận nếu đã đủ")
    clarified_requirement: Optional[str] = Field(description="Bản tóm tắt yêu cầu đầy đủ gồm: Đối tượng, Hành động, Giá trị")

def call_interviewer(user_input: str, history: str = ""):
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        temperature=0.2,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(InterviewResponse)
    
    system_prompt = (
    "Bạn là Senior BA. Nhiệm vụ: Kiểm tra xem yêu cầu có đủ 3 yếu tố (Who, What, Why) chưa.\n"
    "LƯU Ý: Nếu người dùng đã nêu rõ vai trò (Ví dụ: 'Là sinh viên'), hành động ('đăng nhập Google') "
    "và mục đích ('vào hệ thống nhanh'), hãy coi là ĐỦ (is_sufficient = True).\n"
    "Chỉ hỏi thêm nếu yêu cầu cực kỳ ngắn gọn như 'tôi muốn làm chức năng A'."
    )
    
    messages = [
        ("system", system_prompt),
        ("human", f"Lịch sử hội thoại:\n{history}\n\nYêu cầu mới từ người dùng: {user_input}")
    ]
    
    return structured_llm.invoke(messages)