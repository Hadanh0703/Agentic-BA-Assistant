import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vector_db(project_id: int):
    persist_dir = os.path.join("./db_storage", f"project_{project_id}")
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings_model
    )

def ingest_rag_file(file_path: str, project_id: int):
    if not os.path.exists(file_path):
        print(f"Không tìm thấy file tại: {file_path}")
        return

    # --- DỌN DẸP DỮ LIỆU CŨ ---
    persist_dir = os.path.join("./db_storage", f"project_{project_id}")
    if os.path.exists(persist_dir):
        try:
            shutil.rmtree(persist_dir)
            print(f"Đã dọn dẹp tri thức cũ của Project {project_id} để cập nhật bản mới.")
        except Exception as e:
            print(f"Cảnh báo: Không thể xóa thư mục cũ (có thể file đang bị khóa): {e}")

    # 1. Load tài liệu (Hỗ trợ PDF và Text)
    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
    except Exception as e:
        print(f" Lỗi khi đọc file: {e}")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    try:
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings_model,
            persist_directory=persist_dir
        )
        print(f" Project {project_id}: Đã cập nhật tri thức mới thành công!")
    except Exception as e:
        print(f" Lỗi khi khởi tạo Vector DB: {e}")

def query_rag(query: str, project_id: int):
    try:
        persist_dir = os.path.join("./db_storage", f"project_{project_id}")
        
        if not os.path.exists(persist_dir):
            return ""

        vector_db = get_vector_db(project_id)
        
        # Tìm kiếm 3 đoạn văn bản có độ tương đồng cao nhất
        results = vector_db.similarity_search(query, k=3)
        
        context = "\n\n".join([doc.page_content for doc in results])
        return context
    except Exception as e:
        print(f" Lỗi khi truy vấn RAG: {e}")
        return ""