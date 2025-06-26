from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./flowstate.db")

# Handle PostgreSQL connection string special case
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling - OPTIMIZED
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,   
    max_overflow=20,      
    pool_pre_ping=True,   
    pool_recycle=3600,    
    echo=False            
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Optimized dependency with better error handling
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()