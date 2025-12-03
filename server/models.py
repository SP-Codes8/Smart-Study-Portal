from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey
from database import Base

class Student(Base):
    __tablename__ = "Students"

    # Registration number as primary key
  
    name = Column(String, nullable=False)
    register_no = Column(String, primary_key=True, index=True)
    parent_name = Column(String, nullable=False)
    student_class = Column(String, nullable=False)
    password = Column(String, nullable=False)  # store hashed password in production

class Parent(Base):
    __tablename__ = "Parents"

    parent_name = Column(String, primary_key=True, index=True)
    phone_number = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False) 

class Summary(Base):
    __tablename__ = "Summary"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_register_no = Column(String, ForeignKey("Students.register_no"), nullable=False)
    image_data = Column(LargeBinary, nullable=False)  # store the actual image bytes
    image_name = Column(String, nullable=False)        # original filename
    description = Column(String, nullable=True)   