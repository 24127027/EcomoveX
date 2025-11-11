#!/usr/bin/env python3
"""
Generate sample data for testing clustering functionality.
Creates users with diverse preferences and activities.
"""

import sys
import asyncio
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
UTC = timezone.utc

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import sessionmaker
from database.user_database import user_engine
from models.user import User, UserActivity, Activity, Rank, Role
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    def __init__(self):
        self.SessionLocal = sessionmaker(bind=user_engine)
        
        # Sample data templates
        self.user_templates = [
            {
                "username": "beach_lover",
                "email": "beach@test.com",
                "temp_min": 25.0, "temp_max": 35.0,
                "budget_min": 500.0, "budget_max": 2000.0,
                "activities": [Activity.save_destination, Activity.search_destination],
                "destinations": [1, 2, 3]  # Beach destinations
            },
            {
                "username": "mountain_explorer",
                "email": "mountain@test.com", 
                "temp_min": 5.0, "temp_max": 20.0,
                "budget_min": 300.0, "budget_max": 1500.0,
                "activities": [Activity.save_destination, Activity.review_destination],
                "destinations": [4, 5, 6]  # Mountain destinations
            },
            {
                "username": "city_wanderer",
                "email": "city@test.com",
                "temp_min": 15.0, "temp_max": 30.0,
                "budget_min": 800.0, "budget_max": 3000.0,
                "activities": [Activity.search_destination, Activity.save_destination, Activity.review_destination],
                "destinations": [7, 8, 9]  # City destinations
            },
            {
                "username": "budget_traveler",
                "email": "budget@test.com",
                "temp_min": 10.0, "temp_max": 25.0,
                "budget_min": 100.0, "budget_max": 800.0,
                "activities": [Activity.search_destination],
                "destinations": [10, 11]  # Budget destinations
            },
            {
                "username": "luxury_seeker", 
                "email": "luxury@test.com",
                "temp_min": 20.0, "temp_max": 30.0,
                "budget_min": 2000.0, "budget_max": 10000.0,
                "activities": [Activity.save_destination, Activity.review_destination],
                "destinations": [12, 13, 14]  # Luxury destinations
            }
        ]
    
    async def generate_users(self, count: int = 20):
        """Generate sample users with varied preferences."""
        session = self.SessionLocal()
        
        try:
            logger.info(f"Generating {count} sample users...")
            
            # Clear existing test data
            session.query(UserActivity).delete()
            session.query(User).filter(User.email.like('%@test.com')).delete()
            session.commit()
            
            users_created = []
            
            for i in range(count):
                # Choose a template and add variation
                template = random.choice(self.user_templates)
                
                user = User(
                    username=f"{template['username']}_{i+1}",
                    email=f"{template['username']}_{i+1}@test.com",
                    password=generate_password_hash("testpass123"),
                    temp_min=template['temp_min'] + random.uniform(-5, 5),
                    temp_max=template['temp_max'] + random.uniform(-5, 5),
                    budget_min=template['budget_min'] * random.uniform(0.8, 1.2),
                    budget_max=template['budget_max'] * random.uniform(0.8, 1.2),
                    eco_point=random.randint(0, 1000),
                    rank=random.choice(list(Rank)),
                    role=Role.user,
                    created_at=datetime.now(UTC)
                )
                
                session.add(user)
                session.flush()  # Get the user ID
                
                # Generate activities for this user
                await self.generate_activities_for_user(user.id, template, session)
                
                users_created.append(user.id)
            
            session.commit()
            logger.info(f"✅ Created {len(users_created)} users with activities")
            return users_created
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error generating users: {e}")
            raise
        finally:
            session.close()
    
    async def generate_activities_for_user(self, user_id: int, template: dict, session):
        """Generate activities for a specific user based on template."""
        
        # Generate 5-15 activities per user
        num_activities = random.randint(5, 15)
        
        for _ in range(num_activities):
            # Choose activity type from template
            activity_type = random.choice(template['activities'])
            
            # Choose destination from template with some variation
            if random.random() < 0.8:  # 80% from template
                destination_id = random.choice(template['destinations'])
            else:  # 20% random destination
                destination_id = random.randint(1, 20)
            
            # Random timestamp within last 30 days
            timestamp = datetime.now(UTC) - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            activity = UserActivity(
                user_id=user_id,
                destination_id=destination_id,
                activity=activity_type,
                timestamp=timestamp
            )
            
            session.add(activity)
    
    async def display_generated_data(self):
        """Display summary of generated data."""
        session = self.SessionLocal()
        
        try:
            logger.info("📊 Generated Data Summary:")
            
            users = session.query(User).filter(User.email.like('%@test.com')).all()
            logger.info(f"   Total test users: {len(users)}")
            
            # Group users by preferences
            temp_groups = {}
            budget_groups = {}
            
            for user in users:
                # Temperature preference groups
                temp_key = f"{int(user.temp_min)}-{int(user.temp_max)}°C"
                temp_groups[temp_key] = temp_groups.get(temp_key, 0) + 1
                
                # Budget preference groups  
                budget_key = f"${int(user.budget_min)}-${int(user.budget_max)}"
                budget_groups[budget_key] = budget_groups.get(budget_key, 0) + 1
            
            logger.info("   Temperature preferences:")
            for temp_range, count in sorted(temp_groups.items()):
                logger.info(f"     {temp_range}: {count} users")
            
            logger.info("   Budget preferences:")
            for budget_range, count in sorted(budget_groups.items())[:5]:  # Top 5
                logger.info(f"     {budget_range}: {count} users")
            
            # Activity summary
            total_activities = session.query(UserActivity).count()
            activity_types = session.query(UserActivity.activity, session.query(UserActivity).filter_by(activity=UserActivity.activity).count().label('count')).group_by(UserActivity.activity).all()
            
            logger.info(f"   Total activities: {total_activities}")
            
        except Exception as e:
            logger.error(f"Error displaying data summary: {e}")
        finally:
            session.close()

async def main():
    """Main function to generate sample data."""
    print("🎲 EcomoveX Sample Data Generator")
    print("=" * 50)
    
    generator = SampleDataGenerator()
    
    try:
        # Generate sample users
        user_ids = await generator.generate_users(count=25)
        
        # Display summary
        await generator.display_generated_data()
        
        print("\n✅ Sample data generation completed!")
        print("🚀 You can now run: python scripts/test_clustering_local.py")
        
    except Exception as e:
        print(f"\n❌ Sample data generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())