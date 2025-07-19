from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ SQLite DB connection URL (you can change to PostgreSQL/MySQL if needed)
SQLALCHEMY_DATABASE_URL = "sqlite:///./community.db"

# ✅ Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# ✅ SessionLocal class used for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Base class for declaring models
Base = declarative_base()

# ✅ Dependency for injecting DB session into routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
