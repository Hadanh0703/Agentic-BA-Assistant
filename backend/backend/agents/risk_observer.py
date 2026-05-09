import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

class RiskReport(BaseModel):
    is_safe: bool = Field(description="True nếu danh sách task đạt chuẩn")
    red_flags: List[str] = Field(description="Danh sách các điểm yếu, rủi ro hoặc thiếu sót")
    recommendations: str = Field(description="Hướng dẫn cụ thể cho Architect")

async def call_risk_observer_async(tasks_obj) -> RiskReport:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(RiskReport)

    try:
        task_summary = "\n".join([
            f"- [{t.type}] {t.title}: {t.description}"
            for t in tasks_obj.tasks
        ])
    except Exception as e:
        print(f"Risk Observer Error: Không thể đọc danh sách task. {e}")
        task_summary = "Lỗi dữ liệu đầu vào."

    system_prompt = """Bạn là một Senior QA Manager & Security Engineer. 
Nhiệm vụ của bạn là kiểm duyệt danh sách Technical Tasks từ Architect gửi tới.

## TIÊU CHÍ ĐÁNH GIÁ (PHẢI TUÂN THỦ):
1. TÍNH CHI TIẾT: Nếu mô tả task quá sơ sài (không nói rõ dùng API gì, bảng DB nào, hay logic gì) -> is_safe = False.
2. TÍNH CÂN BẰNG: Một tính năng hoàn chỉnh thường cần sự phối hợp giữa DB, BE và FE. Nếu thiếu một trong các lớp này -> is_safe = False.
3. BẢO MẬT & HIỆU NĂNG: Nếu các task liên quan đến dữ liệu nhạy cảm (như mật khẩu, tiền bạc, QR) mà không có task về validate/security -> is_safe = False.
4. KHẢ THI: Nếu task quá lớn (phức tạp) mà không được chia nhỏ -> is_safe = False.

## CÁCH PHẢN HỒI:
- Nếu tất cả OK: is_safe = True, risks = [], recommendations = "Good to go".
- Nếu có lỗi: Liệt kê rõ các rủi ro vào 'risks' và viết hướng dẫn sửa chi tiết vào 'recommendations' để Architect sửa lại.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Danh sách Tasks cần duyệt:\n{task_summary}")
    ]

    return await structured_llm.ainvoke(messages)