import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_database = os.getenv("MYSQL_DATABASE")
    if not mysql_host or not mysql_user or not mysql_database:
        raise RuntimeError(
            "Configure DATABASE_URL ou MYSQL_HOST, MYSQL_USER e MYSQL_DATABASE "
            "no ambiente ou no arquivo .env."
        )
    DATABASE_URL = URL.create(
        "mysql+pymysql",
        username=mysql_user,
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=mysql_host,
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=mysql_database,
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão do banco e a fecha ao final da requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()