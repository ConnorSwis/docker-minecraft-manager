from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///server-storage.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Server(Base):
    __tablename__ = "servers"

    unique_id = Column(String, primary_key=True, index=True)
    container_id = Column(String, index=True)
    game_port = Column(String)
    rcon_port = Column(String)
    rcon_password = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
