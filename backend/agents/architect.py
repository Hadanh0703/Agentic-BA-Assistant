import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from schema import TaskListData as TaskList
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
        query = f"{user_story_obj.role} {user_story_obj.action} {user_story_obj.benefit}"
        related_docs = db.similarity_search(query, k=5)
        rag_context = "\n---\n".join([doc.page_content for doc in related_docs])
        has_rag = bool(rag_context.strip())
    except Exception as e:
        print(f" Architect RAG Error: {e}")
        rag_context = ""
        has_rag = False

    rag_instruction = f"""
## TÀI LIỆU DỰ ÁN (BẮT BUỘC ĐỌC KỸ):
{rag_context}

## QUY TẮC SỬ DỤNG TÀI LIỆU (QUAN TRỌNG):
- Tài liệu trên là nguồn sự thật duy nhất về nghiệp vụ và kỹ thuật của dự án
- PHẢI trích xuất và áp dụng các thông tin sau từ tài liệu vào Task:
  * Quy trình nghiệp vụ cụ thể (ví dụ: QR động 30 giây, offline mode...)
  * Ràng buộc kỹ thuật (ví dụ: mã hóa ngân hàng, tích hợp phần cứng...)
  * Các role và đối tượng liên quan
- KHÔNG được tự bịa ra quy trình nếu tài liệu đã định nghĩa rõ
- Nếu tài liệu nhắc đến công nghệ/quy trình cụ thể → PHẢI đưa vào description của Task
""" if has_rag else """
## LƯU Ý: Không có tài liệu dự án. Hãy dùng best practices phổ biến nhất.
"""

    system_content = f"""Bạn là Senior Solution Architect. Nhiệm vụ: Phân rã User Story thành Technical Tasks chi tiết.

{rag_instruction}

## QUY TẮC PHÂN RÃ TASK:
1. Mỗi Task PHẢI có description cụ thể, nhắc đến nghiệp vụ/công nghệ từ tài liệu dự án
2. Story Points: 1=30ph, 2=2h, 3=nửa ngày, 5=1 ngày, 8=2 ngày (KHÔNG quá 8)
3. Phân loại: FE (giao diện), BE (logic/API), DB (database/migration)
4. Phải có đủ 3 layer FE + BE + DB — thiếu layer nào phải giải thích lý do
5. KHÔNG tạo 2 task trùng chức năng — nếu tách phải khác nhau rõ ràng về scope:
   Tốt: "Xây dựng API validate coupon" vs "Tích hợp coupon vào checkout + cập nhật đơn hàng"
   Xấu: "Xây dựng API kiểm tra mã" vs "Tích hợp API kiểm tra mã" (trùng ý)
6. DB task PHẢI liệt kê đủ tất cả bảng liên quan, bao gồm bảng tracking/history nếu có
   nghiệp vụ kiểm tra trạng thái (đã dùng, đã thanh toán, lịch sử...)
7. Priority theo nguyên tắc:
   - High: blocking task khác, hoặc liên quan security/auth/payment/error handling critical
   - Medium: core feature, không blocking
   - Low: UI polish, redirect, thông báo thành công
"""

    if feedback:
        system_content += f"\n\n## PHẢI GIẢI QUYẾT FEEDBACK TỪ RISK OBSERVER:\n{feedback}"

    user_story_str = f"As a {user_story_obj.role}, I want to {user_story_obj.action} so that {user_story_obj.benefit}"
    ac_str = "\n".join([f"- {ac}" for ac in user_story_obj.acceptance_criteria])

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"""Hãy phân rã User Story sau thành Technical Tasks.
LƯU Ý: Mọi Task PHẢI phản ánh đúng nghiệp vụ từ tài liệu dự án đã cung cấp.

User Story: {user_story_str}
Acceptance Criteria:
{ac_str}""")
    ]

    return await structured_llm.ainvoke(messages)