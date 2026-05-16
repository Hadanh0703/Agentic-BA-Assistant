import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union 

load_dotenv()

class InterviewResponse(BaseModel):
    response_type: Literal["interview_question", "story_draft"] = Field(
        description="'interview_question' nếu cần hỏi thêm, 'story_draft' nếu đã đủ thông tin"
    )
    is_sufficient: Union[bool, str] = Field(description="True nếu đã đủ Who/What/Why để chốt, hoặc chuỗi 'True'/'False'")
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

    system_prompt = f"""Bạn là Senior BA (Business Analyst). Nhiệm vụ DUY NHẤT: Xác định đủ 3 yếu tố WHO/WHAT/WHY và RÀNG BUỘC NGHIỆP VỤ liên quan để chốt yêu cầu.

## TÀI LIỆU DỰ ÁN (RAG):
{context_rag if context_rag else "Không có tài liệu."}

## QUY TẮC ĐÁNH GIÁ (is_sufficient = True/False):
Bạn chỉ được CHỐT (is_sufficient = True) khi đáp ứng ĐẦY ĐỦ các điều kiện sau:
1. Biết WHO: Đối tượng sử dụng tính năng (Khách hàng, Admin, Quản lý...).
2. Biết WHAT: Hành động cụ thể và CÁCH XỬ LÝ LUẬT KINH DOANH. 
   - ĐẶC BIỆT LƯU Ý: Nếu hành động liên quan đến một quy định trong TÀI LIỆU DỰ ÁN (RAG) có phân chia trường hợp/điều kiện (Ví dụ: quy định hủy lịch theo mốc giờ 24h/12h, quy định giảm giá theo hạng thành viên Bạc/Vàng), nhưng người dùng nhập chung chung, chưa làm rõ sẽ xử lý các mốc điều kiện đó ra sao -> BẮT BUỘC ĐÁNH GIÁ IS_SUFFICIENT = FALSE để hỏi lại.
3. Biết WHY: Mục đích/lợi ích mang lại.

## QUY TẮC CHỐNG LOOP:
- Nếu lịch sử hội thoại (history) cho thấy user cố tình từ chối cung cấp thêm hoặc khẳng định "chỉ cần làm thế này" -> Lúc đó mới PHẢI CHỐT với thông tin hiện có.

## TUYỆT ĐỐI KHÔNG HỎI VỀ KỸ THUẬT (Đây là việc của Architect):
- Không hỏi về cách lưu trữ database, bảng dữ liệu.
- Không hỏi về công nghệ (JWT, Mã hóa, API gì...).
- Không hỏi về luồng dữ liệu (Data flow).

## CHỈ HỎI LÀM RÕ NGHIỆP VỤ:
- Hỏi về đối tượng (WHO) hoặc mục đích (WHY) nếu thiếu.
- Hỏi cách xử lý các trường hợp, các mốc ràng buộc quy định dựa theo TÀI LIỆU DỰ ÁN nếu yêu cầu của user đang bị quá chung chung.

## VÍ DỤ:
Context RAG có quy định: "Hủy trước 24h hoàn 100%, trước 12h hoàn 50%, dưới 12h không hoàn".
Input: "Tôi muốn làm tính năng hủy lịch đặt sân và hệ thống tự động hoàn tiền."
-> Phân tích: WHO là Tôi. WHY là để hoàn tiền. WHAT là hủy lịch hoàn tiền nhưng CHƯA RÕ xử lý các mốc hoàn tiền 100%, 50% theo quy định như thế nào.
-> is_sufficient = False.
-> response_type = "interview_question"
-> feedback = "Theo tài liệu dự án, việc hoàn tiền khi hủy lịch phụ thuộc vào thời gian hủy (hoàn 100% trước 24h, 50% trước 12h). Bạn có muốn tính năng tự động hoàn tiền này tự động áp dụng chính xác theo các mốc thời gian quy định này không?"

## KHI CHỐT (is_sufficient = True):
- response_type = "story_draft"
- clarified_requirement = "Đối tượng: [WHO]. Hành động: [WHAT - ghi rõ cách xử lý các rule bám sát RAG]. Mục đích: [WHY]."

## NGÔN NGỮ: Tiếng Việt 100%."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Lịch sử hội thoại:\n{history}\n\nYêu cầu hiện tại: {user_input}")
    ]

    result = await structured_llm.ainvoke(messages)

    if hasattr(result, "is_sufficient") and isinstance(result.is_sufficient, str):
        result.is_sufficient = (result.is_sufficient.lower().strip() == "true")

    return result