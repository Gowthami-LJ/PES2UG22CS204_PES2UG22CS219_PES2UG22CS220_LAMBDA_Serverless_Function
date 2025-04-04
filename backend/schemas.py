from pydantic import BaseModel

class FunctionBase(BaseModel):
    name: str
    route: str
    language: str
    timeout: int

class FunctionCreate(FunctionBase):
    pass

class Function(FunctionBase):
    id: int

    class Config:
        orm_mode = True

