from utils.database import engine, Base, SessionLocal
import sys

def test_connection():
    try:
        # Try to connect
        connection = engine.connect()
        print("✅ Successfully connected to database")
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Successfully created tables")
        
        # Try to open a session
        session = SessionLocal()
        session.close()
        print("✅ Successfully created session")
        
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)