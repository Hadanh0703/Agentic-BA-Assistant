import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings  

load_dotenv()

embeddings_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def get_vector_db(project_id: int):
    persist_dir = os.path.join("./db_storage", f"project_{project_id}")
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings_model
    )

def ingest_rag_file(file_path: str, project_id: int):
    if not os.path.exists(file_path):
        return

    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    try:
        vector_db = get_vector_db(project_id)
        vector_db.add_documents(chunks)
        print(f"Project {project_id}: Đã nạp thêm tri thức từ {os.path.basename(file_path)}")
    except Exception as e:
        print(f"Lỗi khi cập nhật Vector DB: {e}")

def delete_rag_file(file_name: str, project_id: int):
    try:
        vector_db = get_vector_db(project_id)
        vector_db.delete(where={"source": file_name})
        print(f"Đã xóa tri thức của file {file_name} trong Project {project_id}")
    except Exception as e:
        print(f"Lỗi khi xóa tri thức file: {e}")

def query_rag(query: str, project_id: int):
    try:
        persist_dir = os.path.join("./db_storage", f"project_{project_id}")
        if not os.path.exists(persist_dir):
            return ""
        vector_db = get_vector_db(project_id)
        results = vector_db.similarity_search(query, k=5)
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        print(f"Lỗi khi truy vấn RAG: {e}")
        return ""