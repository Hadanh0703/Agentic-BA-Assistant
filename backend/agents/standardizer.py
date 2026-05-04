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

    messages = [
        SystemMessage(content=(
            "Bạn là chuyên gia soạn thảo User Story. "
            "Chuyển nội dung thành format chuẩn Agile kèm AC cụ thể. Tất cả bằng Tiếng Anh."
        )),
        HumanMessage(content=f"Yêu cầu đã làm rõ: {clarified_req}")
    ]
    return await structured_llm.ainvoke(messages)