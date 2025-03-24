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

# Define the Order model
class RunnerReview(Base):
    __tablename__ = 'runner_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    runner_id = Column(BigInteger, nullable=False)  # Telegram ID of the runner
    user_id = Column(BigInteger, nullable=False)  # Telegram ID of the user who gave the review
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    rating = Column(Float, nullable=False)  # Rating from 1 to 5
    comment = Column(String, nullable=True)

SGT = pytz.timezone("Asia/Singapore")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    location = Column(String, nullable=True)
    time = Column(String, nullable=True)
    details = Column(String, nullable=True)
    delivery_fee = Column(String, nullable=True)
    claimed = Column(Boolean, default=False)
    user_id = Column(BigInteger, nullable=False)
    runner_id = Column(BigInteger, nullable=True)
    user_handle = Column(String, nullable=True)
    runner_handle = Column(String, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    order_placed_time = Column(DateTime, default=lambda: datetime.now(SGT))  
    order_claimed_time = Column(DateTime, nullable=True)
    
class StripeAccount(Base):
    __tablename__ = 'stripe_accounts'
    telegram_id = Column(BigInteger, primary_key=True)
    stripe_account_id = Column(String, nullable=False)

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