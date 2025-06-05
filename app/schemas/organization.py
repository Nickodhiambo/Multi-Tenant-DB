from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrganizationCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    owner_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True