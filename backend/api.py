from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import Function, SessionLocal

router = APIRouter()

class FunctionCreate(BaseModel):
    name: str
    language: str
    code: str
    timeout: int

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/functions/")
def create_function(func: FunctionCreate, db: Session = Depends(get_db)):
    db_func = Function(**func.dict())
    try:
        db.add(db_func)
        db.commit()
        db.refresh(db_func)
        return {"message": "Function saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/functions/{name}")
def get_function(name: str, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@router.put("/functions/{name}")
def update_function(name: str, updated: FunctionCreate, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    for field, value in updated.dict().items():
        setattr(func, field, value)
    db.commit()
    return {"message": "Function updated"}

@router.delete("/functions/{name}")
def delete_function(name: str, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    db.delete(func)
    db.commit()
    return {"message": "Function deleted"}
    

