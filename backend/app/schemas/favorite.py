from pydantic import BaseModel
import uuid
from datetime import datetime

from app.schemas.prediction import PredictionListItem

class FavoriteResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime
    prediction: PredictionListItem | None = None

    class Config:
        from_attributes = True
