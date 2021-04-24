from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DBModel(BaseModel):
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()
    deleted: bool = False
