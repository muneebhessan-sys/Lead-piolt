from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_kwargs = {
    "future": True,
    "echo": settings.database_echo,
    "pool_pre_ping": True,
}
if connect_args:
    engine_kwargs["connect_args"] = connect_args
if not settings.database_url.startswith("sqlite"):
    engine_kwargs["pool_size"] = settings.database_pool_size
    engine_kwargs["max_overflow"] = settings.database_max_overflow
    engine_kwargs["pool_timeout"] = settings.database_pool_timeout

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
