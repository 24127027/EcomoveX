from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from database.db import Base
import json

class DestinationEmbedding(Base):
    __tablename__ = "destination_embeddings"

    destination_id = Column(String(255), primary_key=True)
    embedding_vector = Column(Text, nullable=False)  # lưu JSON
    model_version = Column(String(50), default="v1")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # helper để convert list <-> JSON
    def set_vector(self, vector: list[float]):
        self.embedding_vector = json.dumps(vector)

    def get_vector(self) -> list[float]:
        return json.loads(self.embedding_vector)
