from typing import List
from pydantic import BaseModel, Field, field_validator

class Task(BaseModel):
    title: str = Field(description="Tiêu đề ngắn gọn của task kỹ thuật")
    type: str = Field(description="Loại task: FE, BE, hoặc DB")
    description: str = Field(description="Mô tả chi tiết công việc cần làm")
    story_point: int = Field(description="Độ khó từ 1, 2, 3, 5")
    priority: str = Field(description="Độ ưu tiên: High, Medium, hoặc Low")
    assignee_suggestion: str = Field(description="Gợi ý vai trò thực hiện")

    @field_validator('story_point')
    @classmethod
    def validate_story_point(cls, v):
        allowed = [1, 2, 3, 5, 8]
        if v not in allowed:
            closest = min(allowed, key=lambda x: abs(x - v))
            return closest
        return v

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = ['FE', 'BE', 'DB']
        if v.upper() not in allowed:
            raise ValueError(f"type phải là FE, BE, hoặc DB. Nhận được: {v}")
        return v.upper()

class TaskList(BaseModel):
    tasks: List[Task]