from pydantic import BaseModel
from typing import Optional

class FunctionBase(BaseModel):
    name: str
    code: str
    language: str
    timeout: int
    description: Optional[str] = None
    tags: Optional[str] = None

class FunctionCreate(FunctionBase):
    pass

class Function(FunctionBase):
    id: int
    created_at: Optional[str]

    class Config:
        orm_mode = True

