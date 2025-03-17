from sqlalchemy import create_engine, Column, Integer, String, Boolean, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Initialize SQLAlchemy components
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the Order model
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    location = Column(String, nullable=True)
    time = Column(String, nullable=True)
    claimed = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)
    user_handle = Column(String, nullable=True)

# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)

# Get a session to interact with the database
def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()
