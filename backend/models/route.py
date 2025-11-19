from enum import Enum
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.user_database import UserBase