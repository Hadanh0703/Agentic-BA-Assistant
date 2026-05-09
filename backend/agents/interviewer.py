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
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(InterviewResponse)

    system_prompt = f"""Bạn là một Senior Business Analyst. Nhiệm vụ của bạn là đảm bảo mọi yêu cầu từ người dùng phải ĐỦ CHI TIẾT để đội kỹ thuật có thể lập trình được ngay lập tức.

## TÀI LIỆU DỰ ÁN (RAG):
{context_rag if context_rag else "Không có tài liệu."}

## NGUYÊN TẮC KIỂM TRA YÊU CẦU:
Một yêu cầu được coi là "Đủ" (is_sufficient=True) khi bạn có thể trả lời được 3 câu hỏi:
1. Luồng dữ liệu đi như thế nào? (Workflow)
2. Có ràng buộc nghiệp vụ nào không? (Business Rules/Validation)
3. Kết quả đầu ra là gì? (Output)

## CHIẾN THUẬT PHẢN HỒI:
- Nếu yêu cầu chưa đủ để chia Task (ví dụ: chỉ nói "làm tính năng thanh toán"), hãy set is_sufficient=False và gợi ý các thành phần còn thiếu để người dùng chọn.
- Tuyệt đối không tự bịa ra quy trình nếu tài liệu RAG không nhắc tới. Hãy đặt câu hỏi dưới dạng: "Để tính năng này vận hành mượt mà, chúng ta nên đi theo hướng A hay B?"

## PHÂN LOẠI:
- 'interview_question': Dùng khi bạn thấy chưa đủ cơ sở để chia nhỏ Task kỹ thuật. 
- 'story_draft': Chỉ dùng khi thông tin đã đủ để Architect Agent có thể bóc tách đầu việc rõ ràng.

## LƯU Ý: 
- Trả lời bằng Tiếng Việt 100%.
- Giữ thái độ hỗ trợ, đồng kiến tạo (Collaborative), không hỏi cung.
## LƯU Ý QUAN TRỌNG VỀ ĐỊNH DẠNG:
- Trường 'is_sufficient' PHẢI là giá trị Boolean (true hoặc false), KHÔNG ĐƯỢC để trong dấu ngoặc kép.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Lịch sử hội thoại:\n{history}\n\nYêu cầu hiện tại của User: {user_input}")
    ]
    
    return await structured_llm.ainvoke(messages)