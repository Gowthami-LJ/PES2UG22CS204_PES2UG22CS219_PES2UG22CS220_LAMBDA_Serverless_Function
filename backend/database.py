from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./functions.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Function(Base):
    __tablename__ = "functions"

    name = Column(String, primary_key=True, index=True)
    language = Column(String)
    code = Column(String)
    timeout = Column(Integer)

def create_tables():
    Base.metadata.create_all(bind=engine)
