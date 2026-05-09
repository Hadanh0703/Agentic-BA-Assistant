import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from schema import TaskList
from ingest_data import get_vector_db

load_dotenv()

async def call_architect_async(user_story_obj, project_id: int, feedback: str = None) -> TaskList:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        temperature=0.1, 
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(TaskList)
    try:
        db = get_vector_db(project_id)
        query = f"{user_story_obj.action} {user_story_obj.benefit}"
        related_docs = db.similarity_search(query, k=3)
        rag_context = "\n".join([doc.page_content for doc in related_docs])
    except Exception as e:
        print(f" Architect RAG Error: {e}")
        rag_context = "Không tìm thấy tài liệu liên quan."

    system_content = f"""Bạn là một Senior Solution Architect chuyên nghiệp.
Nhiệm vụ: Phân rã User Story thành các Technical Tasks chi tiết cho Team.

## KIẾN THỨC TỪ TÀI LIỆU DỰ ÁN (RAG):
{rag_context}

## QUY TẮC PHÂN RÃ:
1. Chia nhỏ Task sao cho không quá 8 Story Points (SP).
2. Phân loại rõ ràng: FE (Frontend), BE (Backend), DB (Database).
3. Mỗi Task phải có mô tả kỹ thuật cụ thể (Dùng ngôn ngữ lập trình/Framework trong context nếu có).
"""

    if feedback:
        system_content += f"\n\n## FEEDBACK CẦN SỬA TỪ RISK OBSERVER:\n{feedback}"

    user_story_str = f"As a {user_story_obj.role}, I want to {user_story_obj.action} so that {user_story_obj.benefit}"
    
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"User Story: {user_story_str}\nAcceptance Criteria: {user_story_obj.acceptance_criteria}")
    ]

    return await structured_llm.ainvoke(messages)