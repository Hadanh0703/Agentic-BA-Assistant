import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Optional, Literal

load_dotenv()

class InterviewResponse(BaseModel):
    response_type: Literal["answer_from_rag", "interview_question", "story_draft"] = Field(
        description="Loại phản hồi: trả lời dựa trên tài liệu, hỏi thêm thông tin, hoặc đưa ra bản thảo User Story"
    )
    is_sufficient: bool = Field(description="True nếu thông tin đã đủ để chốt yêu cầu")
    feedback: str = Field(description="Nội dung trả lời trực tiếp hoặc câu hỏi làm rõ")
    clarified_requirement: Optional[str] = Field(description="Tóm tắt yêu cầu đầy đủ nếu đã chốt xong")

async def call_interviewer_async(user_input: str, history: str = "", context_rag: str = "") -> InterviewResponse:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        temperature=0.2,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(InterviewResponse)

    system_prompt = 
    f"""Bạn là một Senior Business Analyst (BA) chuyên nghiệp với tư duy hệ thống sắc bén.
        Nhiệm vụ của bạn là phỏng vấn người dùng để làm rõ yêu cầu, đồng thời đóng vai trò là "người gác cổng" để đảm bảo mọi đề xuất đều tuân thủ chặt chẽ với tài liệu dự án (RAG).

## TÀI LIỆU DỰ ÁN HIỆN TẠI (RAG CONTEXT):
{context_rag if context_rag else "Không có tài liệu bổ sung cho dự án này."}

## NGUYÊN TẮC LÀM VIỆC CỐT LÕI:
1. ĐỐI CHIẾU TRƯỚC, TRẢ LỜI SAU: 
   - Trước khi đồng ý với bất kỳ yêu cầu nào, bạn PHẢI kiểm tra tài liệu dự án bên trên.
   - Nếu User yêu cầu SAI quy định (Ví dụ: Đòi mượn 5 cuốn trong khi quy định là 3), bạn PHẢI đính chính ngay bằng số liệu/thông tin cụ thể từ tài liệu.

2. TƯ DUY PHẢN BIỆN (CONSULTING MINDSET):
   - Không máy móc làm theo mọi thứ User nói. 
   - Nếu yêu cầu hợp lý nhưng chưa tối ưu, hãy gợi ý phương án tốt hơn dựa trên context dự án.
   - Luôn giải thích lý do (Tại sao cho phép? Tại sao từ chối?) trước khi đưa ra hành động tiếp theo.

3. KIỂM SOÁT LUỒNG (CHỐNG LOOP):
   - Không hỏi lại những gì đã có trong History hoặc Tài liệu.
   - Mỗi lượt hội thoại chỉ tập trung giải quyết 1 vấn đề cốt lõi nhất.
   - Nếu thông tin đã rõ ràng (~80%) → set is_sufficient = True để chuyển sang soạn User Story.

## CÁCH PHÂN LOẠI RESPONSE_TYPE:
- 'answer_from_rag': Khi User hỏi kiến thức hoặc yêu cầu VI PHẠM tài liệu. Bạn cần trả lời/đính chính dựa trên tài liệu dự án.
- 'story_draft': Khi yêu cầu hợp lệ và đủ thông tin, hãy đưa ra bản thảo (Who/What/Why) để xác nhận.
- 'interview_question': Khi yêu cầu quá mơ hồ, cần đặt câu hỏi thông minh để khơi gợi nghiệp vụ.

## VÍ DỤ TỔNG QUÁT:
- User: "Tôi muốn thêm tính năng X (tài liệu ghi X không được hỗ trợ)."
- Phản hồi: "Hiện tại theo tài liệu dự án, tính năng X chưa được hỗ trợ vì lý do [Dẫn chứng từ RAG]. Thay vào đó, bạn có muốn sử dụng giải pháp Y vốn đã có sẵn để giải quyết vấn đề này không?"
(response_type='answer_from_rag')
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Lịch sử hội thoại:\n{history}\n\nYêu cầu hiện tại của User: {user_input}")
    ]
    
    return await structured_llm.ainvoke(messages)