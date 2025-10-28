from sqlalchemy import Column, Integer, Float
from database.database import Base

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)