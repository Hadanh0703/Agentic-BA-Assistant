import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

load_dotenv()

class QualityReport(BaseModel):
    is_safe: bool = Field(description="True nếu danh sách task ổn. False nếu cần chia nhỏ hoặc sửa lại.")
    red_flags: List[str] = Field(description="Danh sách các điểm rủi ro phát hiện được.")
    recommendations: str = Field(description="Lời khuyên để Architect hoàn thiện danh sách task.")

def call_risk_observer(tasks_obj):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
    structured_llm = llm.with_structured_output(QualityReport)

    task_summary = "\n".join([
        f"- [{t.type}] {t.title} ({t.story_point} SP)\n  Mô tả: {t.description}"
        for t in tasks_obj.tasks
    ])

    system_prompt = (
        "Bạn là Senior QA Manager. Hãy kiểm tra danh sách Technical Tasks sau.\n"
        "Tiêu chí loại bỏ:\n"
        "1. Task >= 8 SP (Quá lớn, cần chia nhỏ).\n"
        "2. Thiếu sự cân bằng giữa FE/BE/DB.\n"
        "3. Mô tả task quá sơ sài, không có tech-stack."
    )

    messages = [
        ("system", system_prompt),
        ("human", f"Danh sách task cần kiểm tra:\n{task_summary}")
    ]
    return structured_llm.invoke(messages)