from pydantic import BaseModel

class Material(BaseModel):
    topic: str
    content: str