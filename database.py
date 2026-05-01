import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "project_management.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                title TEXT,
                type TEXT,
                description TEXT,
                story_point INTEGER,
                priority TEXT,
                assignee TEXT,
                status TEXT DEFAULT 'Todo',
                deadline TEXT
            )
        ''')
        conn.commit()
    print("==> Khởi tạo Database thành công!")

def save_tasks_to_db(task_list, project_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for task in task_list:
            cursor.execute('''
                INSERT INTO tasks (
                    project_name, title, type, description, story_point,
                    priority, assignee, status, deadline
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_name,
                task.title,
                task.type,
                task.description,
                task.story_point,
                task.priority,
                task.assignee_suggestion,
                'Todo',
                None
            ))
        conn.commit()
    print(f"==> Đã lưu {len(task_list)} task vào dự án '{project_name}' thành công!")

def get_all_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
    return [dict(row) for row in rows]

def delete_task(task_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

def clear_all_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
        conn.commit()

def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

if __name__ == "__main__":
    reset_db()