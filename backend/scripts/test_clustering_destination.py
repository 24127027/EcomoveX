import sys
import os

# Add backend folder to path BEFORE any model imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_path)

import asyncio
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User, UserActivity, Activity
from models.destination_embedding import DestinationEmbedding
from models.cluster import Cluster, UserClusterAssociation
from services.embedding_service import (
    embed_user, embed_destination, save_destination_embedding,
    build_all_destination_embeddings, build_faiss_index,
    recommend_for_cluster_hybrid
)

# -----------------------------
# Setup in-memory SQLite DB
# -----------------------------
engine = create_engine("sqlite:///:memory:", echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Create all tables
from database.db import Base
Base.metadata.create_all(bind=engine)

# -----------------------------
# Create dummy users
# -----------------------------
users = []
for i in range(5):
    u = User(
        id=i+1, 
        username=f"user{i+1}",
        email=f"user{i+1}@example.com",  # Added required email field
        password="hashed_password",       # Added password field
        temp_min=15, 
        temp_max=30,
        budget_min=100, 
        budget_max=500, 
        eco_point=random.randint(0,10)
    )
    session.add(u)
    users.append(u)

session.commit()

# -----------------------------
# Create dummy destinations
# -----------------------------
destinations = []
for i in range(10):
    d = {
        "id": f"dest{i+1}",
        "name": f"Destination {i+1}",
        "tags": ["beach", "mountain"] if i % 2 == 0 else ["city", "museum"],
        "description": f"A lovely place number {i+1}"
    }
    destinations.append(d)

# -----------------------------
# Create a dummy cluster
# -----------------------------
cluster = Cluster(id=1, name="Cluster1", algorithm="kmeans")
session.add(cluster)
session.commit()

# Associate users to cluster
for u in users:
    assoc = UserClusterAssociation(user_id=u.id, cluster_id=cluster.id)
    session.add(assoc)
session.commit()

# -----------------------------
# Create dummy user activities
# -----------------------------
activities = [Activity.save_destination, Activity.search_destination, Activity.review_destination]

for u in users:
    for d in destinations:
        act = UserActivity(user_id=u.id, destination_id=d["id"],
                           activity=random.choice(activities))
        session.add(act)

session.commit()

# -----------------------------
# Build destination embeddings
# -----------------------------
print("Building destination embeddings...")
build_all_destination_embeddings(session, destinations)

print("Building FAISS index...")
build_faiss_index(session)

# -----------------------------
# Run hybrid recommendation for the cluster
# -----------------------------
print("\nGenerating hybrid recommendations for cluster...")
recommendations = recommend_for_cluster_hybrid(cluster.id, session, k=5)
print("\nHybrid recommendations for cluster:")
for r in recommendations:
    print(f"  {r}")

print("\n✓ Test completed successfully!")