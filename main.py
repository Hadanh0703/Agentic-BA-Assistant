import os
import sys
from database import init_db, save_tasks_to_db, get_all_tasks, clear_all_tasks
from agents.orchestrator import run_ai_ba_workflow

init_db()

def run_app():
    history = "" 
    
    while True:
        print("\n" + "="*20 + " HỆ THỐNG AI-BA ASSISTANT (MULTI-AGENT) " + "="*20)
        print("1. Nhập yêu cầu & Tự động Phân rã Task (Full Pipeline)")
        print("2. Xem danh sách Task trong Database")
        print("3. Xóa toàn bộ dữ liệu")
        print("q. Thoát hệ thống")
        print("="*56)
        
        choice = input("Lựa chọn của bạn: ")
        
        if choice == '1':
            user_input = input("\nBạn (BA/PM): ")
            
            result = run_ai_ba_workflow(user_input, history)
            
            if result["status"] == "need_more_info":
                print(f"\n AI (Interviewer): {result['feedback']}")
                history += f"\nUser: {user_input}\nAI: {result['feedback']}"
                continue
            
            elif result["status"] == "success":
                print("\n AI ĐÃ HOÀN TẤT PHÂN TÍCH!")
                print("-" * 50)
                us = result["user_story"]
                tasks = result["technical_tasks"]
                risk = result["risk_assessment"]
                
                print(f" USER STORY: As a {us.role}, {us.action}, {us.benefit}")
                print("\n DANH SÁCH TASK KỸ THUẬT (ĐÃ QUA KIỂM ĐỊNH):")
                for i, t in enumerate(tasks):
                    print(f"{i+1}. [{t.type}] {t.title} | {t.story_point} SP | Ưu tiên: {t.priority}")
                    print(f"   Mô tả: {t.description}")
                
                print(f"\n  BÁO CÁO RỦI RO: {'AN TOÀN ' if risk.is_safe else 'CẢNH BÁO '}")
                if not risk.is_safe:
                    print(f"   - Lưu ý: {risk.red_flags}")

                save_tasks_to_db(tasks, us.action[:30])
                print("\n[Hệ thống]: Đã lưu kết quả vào Database thành công!")
                
                history = ""

        elif choice == '2':
            tasks = get_all_tasks()
            if not tasks:
                print("\n[Hệ thống]: Database đang trống.")
            else:
                print("\n" + "-"*15 + " DANH SÁCH TASK ĐÃ LƯU " + "-"*15)
                for t in tasks:
                    print(f"ID: {t['id']} | Project: {t['project_name']} | [{t['type']}] {t['title']} ({t['story_point']} SP)")
                print("-" * 50)

        elif choice == '3':
            confirm = input("\n  Bạn có chắc muốn xóa sạch Database không? (y/n): ")
            if confirm.lower() == 'y':
                clear_all_tasks()
                print("==> Hệ thống đã được dọn dẹp sạch sẽ!")

        elif choice.lower() == 'q':
            print("Đang thoát hệ thống... Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng thử lại.")

if __name__ == "__main__":
    run_app()