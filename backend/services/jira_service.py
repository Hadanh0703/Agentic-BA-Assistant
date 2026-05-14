import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class JiraProvider:
    def __init__(self):
        self.url = os.getenv("JIRA_SITE_URL", "").strip()
        self.email = os.getenv("JIRA_USER_EMAIL", "").strip()
        self.api_token = os.getenv("JIRA_API_TOKEN", "").strip()
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()

        print("\n" + "="*40)
        print(" JIRA CONFIG CHECK:")
        print(f"-> URL      : '{self.url}'")
        print(f"-> Email    : '{self.email}'")
        print(f"-> Project  : '{self.project_key}'")
        print(f"-> Token set: {'' if self.api_token else 'MISSING'}")
        print("="*40 + "\n")

        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_issue(self, summary: str, description: str, issue_type: str = "Story"):
        if not self.url or not self.email or not self.api_token:
            raise Exception(
                f"Thiếu cấu hình Jira: "
                f"URL={'true' if self.url else 'false'}, "
                f"EMAIL={'true' if self.email else 'false'}, "
                f"TOKEN={'true' if self.api_token else 'false'}"
            )

        endpoint = f"{self.url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }

        response = requests.post(
            endpoint, json=payload,
            headers=self.headers, auth=self.auth
        )

        if response.status_code == 400 and issue_type == "Story":
            print(f" 'Story' không hợp lệ, fallback sang 'Task'...")
            print(f"   Jira raw: {response.text}")
            payload["fields"]["issuetype"]["name"] = "Task"
            response = requests.post(
                endpoint, json=payload,
                headers=self.headers, auth=self.auth
            )

        if response.status_code == 201:
            result = response.json()
            print(f" Tạo {issue_type} thành công: {result.get('key')}")
            return result

        try:
            jira_detail = response.json()
            errors = jira_detail.get("errors", {})
            messages = jira_detail.get("errorMessages", [])
            detail = errors or messages or response.text
        except Exception:
            detail = response.text

        print(f" Jira Error {response.status_code}: {detail}")
        raise Exception(f"Jira {response.status_code}: {detail}")

    def get_story_points_field(self) -> str | None:
        """Tự động tìm field ID của Story Points"""
        endpoint = f"{self.url}/rest/api/3/field"
        res = requests.get(endpoint, headers=self.headers, auth=self.auth)

        if res.status_code == 200:
            for field in res.json():
                name = field.get("name", "").lower()
                if "story point" in name or "story_point" in name:
                    print(f" Tìm thấy SP field: '{field['name']}' → ID: {field['id']}")
                    return field["id"]

        print(" Không tìm thấy Story Points field")
        return None

    def update_story_points(self, issue_key: str, field_id: str, story_points: int):
        """Cập nhật SP cho issue đã tạo bằng PUT"""
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}"
        payload = {"fields": {field_id: float(story_points)}}

        res = requests.put(endpoint, json=payload, headers=self.headers, auth=self.auth)
        if res.status_code == 204:
            print(f" Updated SP={story_points} cho {issue_key}")
            return True
        else:
            print(f" Update SP lỗi cho {issue_key}: {res.text}")
            return False

    def get_board_id(self, project_key: str) -> int | None:
        """Tự động tìm board ID từ project key"""
        endpoint = f"{self.url}/rest/agile/1.0/board"
        params = {"projectKeyOrId": project_key}
        res = requests.get(endpoint, headers=self.headers, auth=self.auth, params=params)

        if res.status_code == 200:
            boards = res.json().get("values", [])
            if boards:
                board_id = boards[0]["id"]
                print(f" Tìm thấy board '{boards[0]['name']}' (ID: {board_id}) cho project {project_key}")
                return board_id

        print(f" Không tìm thấy board cho project {project_key}: {res.text}")
        return None

    def create_sprint(self, board_id: int, sprint_name: str) -> int | None:
        """Tạo sprint mới với tên tùy chỉnh"""
        endpoint = f"{self.url}/rest/agile/1.0/sprint"
        payload = {
            "name": sprint_name,
            "originBoardId": board_id,
            "goal": f"Auto-generated by AI-BA Assistant — {sprint_name}"
        }
        res = requests.post(endpoint, json=payload, headers=self.headers, auth=self.auth)
        if res.status_code == 201:
            sprint_id = res.json().get("id")
            print(f" Tạo sprint '{sprint_name}' (ID: {sprint_id})")
            return sprint_id

        print(f" Không tạo được sprint '{sprint_name}': {res.text}")
        return None

    def get_or_create_sprint(self, board_id: int, sprint_name: str = "Sprint 1") -> int | None:
        """Lấy sprint đang active hoặc tạo mới"""
        endpoint = f"{self.url}/rest/agile/1.0/board/{board_id}/sprint"
        res = requests.get(endpoint, headers=self.headers, auth=self.auth)

        if res.status_code == 200:
            sprints = res.json().get("values", [])
            for s in sprints:
                if s.get("state") == "active":
                    print(f" Dùng sprint active: {s['name']} (ID: {s['id']})")
                    return s["id"]
            if sprints:
                latest = sprints[-1]
                print(f" Dùng sprint mới nhất: {latest['name']} (ID: {latest['id']})")
                return latest["id"]

        return self.create_sprint(board_id, sprint_name)

    def move_to_sprint(self, sprint_id: int, issue_keys: list):
        """Move danh sách issue vào sprint"""
        endpoint = f"{self.url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        res = requests.post(
            endpoint,
            json={"issues": issue_keys},
            headers=self.headers, auth=self.auth
        )
        if res.status_code == 204:
            print(f" Moved {len(issue_keys)} issues vào sprint {sprint_id}")
        else:
            print(f" Move sprint lỗi: {res.text}")

    def test_connection(self) -> bool:
        if not self.url:
            return False
        try:
            endpoint = f"{self.url}/rest/api/3/myself"
            res = requests.get(endpoint, headers=self.headers, auth=self.auth)
            return res.status_code == 200
        except Exception:
            return False