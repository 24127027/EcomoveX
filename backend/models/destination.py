from sqlalchemy import Column, Integer, Float, String
from database.destination_database import DestinationBase

class Destination(DestinationBase):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)