from models.order_model import create_tables
from models.order_model import Base
from models.database import engine

# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)

# Call the function to create tables
if __name__ == "__main__":
    create_tables()
