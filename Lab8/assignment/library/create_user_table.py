import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./user.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sqlalchemy.orm.declarative_base()

# Database model definitions
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    fullname = Column(String, nullable=False)
    has_book = Column(Boolean, default=False)

    # Relationship with Borrowlist table (if needed)
    holder = relationship("Borrowlist", back_populates="borrower")


# Create the database and tables
Base.metadata.create_all(bind=engine)
