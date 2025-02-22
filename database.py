import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Sequence
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    claimed = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)  # Store Telegram numeric ID
    user_handle = Column(String, nullable=True)  # Store Telegram username

Base.metadata.create_all(bind=engine)