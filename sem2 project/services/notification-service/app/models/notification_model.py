from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    recipient_id: int
    type: str = Field(..., min_length=1, max_length=50)
    message: str = Field(..., min_length=1, max_length=300)


class NotificationResponse(BaseModel):
    id: str
    recipient_id: int
    type: str
    message: str