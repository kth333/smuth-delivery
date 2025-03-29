from sqlalchemy import create_engine, Column, Integer, String, Boolean, Sequence, ForeignKey, Float, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Initialize SQLAlchemy components
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SGT = pytz.timezone("Asia/Singapore")

# Get a session to interact with the database
def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()