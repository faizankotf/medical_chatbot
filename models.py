from sqlalchemy import Column, String, Integer
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrd_number = Column(String, unique=True, index=True)
    file_path = Column(String)