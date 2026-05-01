import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from schema import TaskList

load_dotenv()

_embeddings = None
_db_instance = None

def get_vector_db(db_path="./db_storage"):
    global _embeddings, _db_instance
    if _db_instance is None:
        print("  [Architect] Đang load HuggingFace model (chỉ load 1 lần)...")
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _db_instance = Chroma(persist_directory=db_path, embedding_function=_embeddings)
    return _db_instance

def call_architect(user_story_obj, db_path="./db_storage", feedback=None):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(TaskList)

    db = get_vector_db(db_path)

    rag_query = f"{user_story_obj.action} {user_story_obj.benefit}"
    related_docs = db.similarity_search(rag_query, k=3)
    rag_context = "\n".join([doc.page_content for doc in related_docs])

    user_story_str = f"As a {user_story_obj.role}, I want to {user_story_obj.action} so that {user_story_obj.benefit}"

    full_system_prompt = (
        "Bạn là Senior Solution Architect. Nhiệm vụ: Phân rã User Story thành Technical Tasks.\n"
        "--- QUY CHUẨN TỪ TÀI LIỆU DỰ ÁN (RAG) ---\n"
        f"{rag_context}\n\n"
        "--- QUY TẮC BẮT BUỘC ---\n"
        "1. KHÔNG ĐƯỢC tạo task nào có Story Point >= 8. Nếu task quá lớn, BẮT BUỘC phải chia thành các task nhỏ hơn.\n"
        "2. Phân loại: [FE], [BE], [DB].\n"
    )

    if feedback:
        full_system_prompt += f"\n--- PHẢN HỒI TỪ RISK AGENT ---\n{feedback}"

    messages = [
        ("system", full_system_prompt),
        ("human", f"User Story: {user_story_str}\nTiêu chí chấp nhận (AC): {user_story_obj.acceptance_criteria}")
    ]
    return structured_llm.invoke(messages)