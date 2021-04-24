from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DBModel(BaseModel):
    created_at: Optional[datetime] = datetime.utcnow()
    updated_at: Optional[datetime] = datetime.utcnow()
    deleted: bool = False
