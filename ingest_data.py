import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

def ingest_rag_file(file_path):
    loader = PyPDFLoader(file_path) if file_path.endswith('.pdf') else TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./db_storage"
    )
    print(f" Đã nạp thành công {len(chunks)} đoạn tri thức vào ChromaDB bằng HuggingFace!")

if __name__ == "__main__":
    ingest_rag_file("./data/Test_Rag.pdf")