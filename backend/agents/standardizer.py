import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

class UserStory(BaseModel):
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[str]

async def call_standardizer_async(clarified_req: str) -> UserStory:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0,
                   groq_api_key=os.getenv("GROQ_API_KEY"))
    structured_llm = llm.with_structured_output(UserStory)

    system_prompt = (
        "Bạn là một chuyên gia Senior Business Analyst chuyên soạn thảo tài liệu nghiệp vụ Agile. "
        "Nhiệm vụ của bạn là chuyển đổi yêu cầu từ ngôn ngữ chat sang User Story chuyên nghiệp.\n\n"
        
        "QUY TẮC SOẠN THẢO:\n"
        "1. ROLE: Linh hoạt giữa 'Người dùng' và các danh xưng phù hợp với ý định của BA'.\n"
        "2. ACTION: Mô tả hành động mang tính hệ thống (ví dụ: 'Thực hiện thanh toán', 'Yêu cầu bảo lưu' thay vì 'Muốn nạp tiền').\n"
        "3. BENEFIT: Đây là phần quan trọng nhất. Không lặp lại Action. Hãy nêu bật GIÁ TRỊ thực tế (ví dụ: 'để tối ưu hóa thời gian tập luyện', 'để thực hiện giao dịch không dùng tiền mặt').\n"
        "4. ACCEPTANCE CRITERIA (AC): Viết theo dạng kiểm thử (Testable). Phải bao gồm cả luồng thành công và luồng lỗi (Validation).\n"
        
        "NGÔN NGỮ: Tiếng Việt 100%. Hành văn sắc sảo, chuyên nghiệp."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Dưới đây là thông tin yêu cầu cần chuẩn hóa:\n{clarified_req}")
    ]
    return await structured_llm.ainvoke(messages)