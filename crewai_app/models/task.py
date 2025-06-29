from pydantic import BaseModel

class Task(BaseModel):
    feature: str
    description: str 