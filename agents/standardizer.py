import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

load_dotenv()

class UserStory(BaseModel):
    role: str = Field(description="Vai trò người dùng: As a [Role]")
    action: str = Field(description="Hành động mong muốn: I want to [Action]")
    benefit: str = Field(description="Lợi ích mang lại: So that [Benefit]")
    acceptance_criteria: List[str] = Field(description="Danh sách ít nhất 3 tiêu chí chấp nhận (AC) chi tiết")

def call_standardizer(clarified_req: str):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(UserStory)
    
    system_prompt = (
        "Bạn là chuyên gia soạn thảo User Story. "
        "Hãy chuyển nội dung sau thành format chuẩn Agile kèm các tiêu chí chấp nhận (AC) cụ thể.\n"
        "Yêu cầu: Viết bằng tiếng Việt chuyên ngành IT."
    )
    
    messages = [
        ("system", system_prompt),
        ("human", f"Nội dung yêu cầu đã làm rõ: {clarified_req}")
    ]
    return structured_llm.invoke(messages)