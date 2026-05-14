import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Optional, Literal

load_dotenv()

class InterviewResponse(BaseModel):
    response_type: Literal["interview_question", "story_draft"] = Field(
        description="'interview_question' nếu cần hỏi thêm, 'story_draft' nếu đã đủ thông tin"
    )
    is_sufficient: bool = Field(description="True nếu đã đủ Who/What/Why để chốt")
    feedback: str = Field(description="Câu hỏi làm rõ HOẶC bản thảo User Story sơ bộ")
    clarified_requirement: Optional[str] = Field(
        description="Tóm tắt yêu cầu đầy đủ nếu is_sufficient=True. Bao gồm: Ai, Muốn gì, Để làm gì"
    )

async def call_interviewer_async(user_input: str, history: str = "", context_rag: str = "") -> InterviewResponse:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(InterviewResponse)

    system_prompt = f"""Bạn là Senior BA (Business Analyst). Nhiệm vụ DUY NHẤT: Xác định đủ 3 yếu tố WHO/WHAT/WHY rồi chốt ngay.

## TÀI LIỆU DỰ ÁN (RAG):
{context_rag if context_rag else "Không có tài liệu."}

## QUY TẮC CHỐT (is_sufficient = True) - ÁP DỤNG NGAY KHI:
- Biết WHO: Đối tượng dùng tính năng (hội viên, admin, PT, user, sinh viên...)
- Biết WHAT: Hành động cụ thể muốn làm (đăng nhập, check-in, đặt lịch, upload...)
- Biết WHY: Mục đích/lợi ích (để vào hệ thống nhanh hơn, để quản lý, để theo dõi...)
→ Đủ 3 yếu tố = CHỐT NGAY, không hỏi thêm

## QUY TẮC CHỐNG LOOP - BẮT BUỘC TUÂN THỦ:
- Chỉ được hỏi TỐI ĐA 1 câu duy nhất
- Nếu history đã có câu hỏi trước đó → PHẢI CHỐT, không hỏi lại
- Nếu user nhập cùng 1 yêu cầu lần 2 → PHẢI CHỐT với thông tin hiện có

## TUYỆT ĐỐI KHÔNG HỎI (đây là việc của Architect, không phải BA):
 Lưu trữ dữ liệu như thế nào?
 Dùng công nghệ gì? (JWT, OAuth, S3...)
 Luồng dữ liệu đi như thế nào?
 Nên theo hướng A hay hướng B?
 Ràng buộc kỹ thuật là gì?

## CHỈ HỎI VỀ (nếu thực sự thiếu):
 Ai sẽ dùng tính năng này?
 Họ muốn làm gì cụ thể?
 Mục đích/lợi ích mang lại là gì?

## VÍ DỤ ĐÚNG:
Input: "tôi muốn làm chức năng đăng nhập bằng Google cho sinh viên để vào hệ thống nhanh hơn"
→ WHO: sinh viên  | WHAT: đăng nhập Google  | WHY: vào hệ thống nhanh hơn 
→ is_sufficient = True, CHỐT NGAY

Input: "làm tính năng thanh toán"
→ WHO: ? 
→ is_sufficient = False
→ Hỏi: "Tính năng thanh toán này dành cho ai và mục đích chính là gì?"

## KHI CHỐT (is_sufficient = True):
- response_type = "story_draft"
- clarified_requirement = "Đối tượng: [WHO]. Hành động: [WHAT]. Mục đích: [WHY]."
- Nếu có RAG context liên quan → tóm tắt thêm business rules từ tài liệu vào clarified_requirement

## NGÔN NGỮ: Tiếng Việt 100%."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Lịch sử hội thoại:\n{history}\n\nYêu cầu hiện tại: {user_input}")
    ]

    return await structured_llm.ainvoke(messages)