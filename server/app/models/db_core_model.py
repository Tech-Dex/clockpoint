from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DBCoreModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = datetime.utcnow()
    updated_at: Optional[datetime] = datetime.utcnow()
    deleted_at: Optional[datetime] = None
