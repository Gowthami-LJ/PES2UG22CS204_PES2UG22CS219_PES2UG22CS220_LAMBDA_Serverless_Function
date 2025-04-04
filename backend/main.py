from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import Function, SessionLocal, create_tables

app = FastAPI()
create_tables()

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

@app.post("/functions/")
async def create_function(func: FunctionCreate, db: Session = Depends(get_db)):
    db_func = Function(**func.dict())
    try:
        db.add(db_func)
        db.commit()
        db.refresh(db_func)
        return {"message": "Function saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/functions/{name}")
async def get_function(name: str, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@app.put("/functions/{name}")
async def update_function(name: str, updated: FunctionCreate, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    for field, value in updated.dict().items():
        setattr(func, field, value)
    db.commit()
    return {"message": "Function updated"}

@app.delete("/functions/{name}")
async def delete_function(name: str, db: Session = Depends(get_db)):
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    db.delete(func)
    db.commit()
    return {"message": "Function deleted"}
    
@app.post("/functions/execute/{name}")
async def execute_function(name: str, db: Session = Depends(get_db)):
    # Get the function from the database
    func = db.query(Function).filter(Function.name == name).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # Import the runner and execute the function
    from virtualization.runner import run_in_docker
    result = run_in_docker(func.code, func.language, func.timeout)
    
    return {
        "function_name": name,
        "language": func.language,
        "result": result
    }
