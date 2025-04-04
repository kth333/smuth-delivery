from sqlalchemy import Column, Integer, String, Boolean, Sequence, ForeignKey, Float, BigInteger, DateTime
from .database import Base, SGT
from datetime import datetime

# Define the Order model
class RunnerReview(Base):
    __tablename__ = 'runner_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    runner_id = Column(BigInteger, nullable=False)  # Telegram ID of the runner
    user_id = Column(BigInteger, nullable=False)  # Telegram ID of the user who gave the review
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    rating = Column(Float, nullable=False)  # Rating from 1 to 5
    comment = Column(String, nullable=True)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    location = Column(String, nullable=True)
    time = Column(String, nullable=True)
    earliest_pickup_time = Column(DateTime(timezone=True), nullable=True)
    latest_pickup_time = Column(DateTime(timezone=True), nullable=True)
    details = Column(String, nullable=True)
    delivery_fee = Column(String, nullable=True)
    claimed = Column(Boolean, default=False)
    expired = Column(Boolean, default=False)
    user_id = Column(BigInteger, nullable=False)
    runner_id = Column(BigInteger, nullable=True)
    user_handle = Column(String, nullable=True)
    runner_handle = Column(String, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    order_placed_time = Column(DateTime(timezone=True), default=lambda: datetime.now(SGT))  
    order_claimed_time = Column(DateTime(timezone=True), nullable=True)
    channel_message_id = Column(Integer, nullable=True)
    
class StripeAccount(Base):
    __tablename__ = 'stripe_accounts'
    telegram_id = Column(BigInteger, primary_key=True)
    stripe_account_id = Column(String, nullable=False)
    
class ReportUser(Base):
    __tablename__ = 'report_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, nullable=False)
    order_id = Column(Integer, nullable=False)
    reported_user_id = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(SGT))
    
# class ReportBugs(Base):
#     __tablename__ = 'report_bugs'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     reporter_id = Column(BigInteger, nullable=False)
#     bug_description = Column(String, nullable=False)
#     timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(SGT))

# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)
    