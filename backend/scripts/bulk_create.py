from sqlalchemy.ext.asyncio import AsyncSession
from models.user import Rank, Activity
from repository.user_repository import UserRepository
from repository.cluster_repository import ClusterRepository
from schemas.authentication_schema import UserRegister
from schemas.destination_schema import DestinationCreate, DestinationEmbeddingCreate
from schemas.map_schema import AutocompleteRequest
from schemas.user_schema import UserActivityCreate
from services.authentication_service import AuthenticationService
from services.destination_service import DestinationService
from services.map_service import MapService
from services.user_service import UserService
from services.cluster_service import ClusterService
import random


# Sample users data (59 users with diverse preferences)
SAMPLE_USERS = [
    # Beach lovers
    {"username": "NguyenVanAn", "email": "nguyenvanan@gmail.com", "password": "password123", "rank": Rank.silver,
     "preference": {"weather_pref": {"min_temp": 22, "max_temp": 32}, "attraction_types": ["beach", "park", "zoo", "museum"],
                   "budget_range": {"min": 500, "max": 2000}, "kids_friendly": True}},
    {"username": "TranThiBich", "email": "tranthibich@gmail.com", "password": "password123", "rank": Rank.silver,
     "preference": {"weather_pref": {"min_temp": 20, "max_temp": 30}, "attraction_types": ["beach", "resort", "water_park", "aquarium"],
                   "budget_range": {"min": 800, "max": 3000}, "kids_friendly": True}},
    
    # Mountain/Adventure lovers
    {"username": "LeHoangPhong", "email": "lehoangphong@gmail.com", "password": "password123", "rank": Rank.gold,
     "preference": {"weather_pref": {"min_temp": 15, "max_temp": 25}, "attraction_types": ["mountain", "hiking", "camping", "waterfall"],
                   "budget_range": {"min": 200, "max": 800}, "kids_friendly": False}},
    {"username": "PhamMinhTuan", "email": "phamminhtuan@gmail.com", "password": "password123", "rank": Rank.gold,
     "preference": {"weather_pref": {"min_temp": 10, "max_temp": 22}, "attraction_types": ["mountain", "trekking", "cave", "forest"],
                   "budget_range": {"min": 150, "max": 600}, "kids_friendly": False}},
]  # Truncated for brevity - add remaining 55 users as needed


# Vietnamese locations for autocomplete searches
VIETNAM_LOCATIONS = [
    # Major cities
    "Ho Chi Minh City Vietnam", "Hanoi Vietnam", "Da Nang Vietnam", "Hai Phong Vietnam", "Can Tho Vietnam",
    
    # Popular tourist destinations
    "Hoi An Vietnam", "Hue Vietnam", "Nha Trang Vietnam", "Phu Quoc Island Vietnam", "Dalat Vietnam",
    "Sapa Vietnam", "Ha Long Bay Vietnam", "Ninh Binh Vietnam", "Vung Tau Vietnam", "Mui Ne Vietnam",
    
    # Cultural sites
    "Hue Imperial City Vietnam", "My Son Sanctuary Vietnam", "Cu Chi Tunnels Vietnam", "Mekong Delta Vietnam",
    "Phong Nha Ke Bang National Park Vietnam", "Cat Ba Island Vietnam", "Con Dao Vietnam",
    
    # Beach destinations
    "Nha Trang Beach Vietnam", "Phu Quoc Beach Vietnam", "Mui Ne Beach Vietnam", "Da Nang Beach Vietnam",
    "Quy Nhon Beach Vietnam", "Vung Tau Beach Vietnam", "Phan Thiet Beach Vietnam",
    
    # Mountain destinations
    "Sapa Mountain Vietnam", "Dalat Highlands Vietnam", "Ha Giang Loop Vietnam", "Fansipan Mountain Vietnam",
    "Moc Chau Vietnam", "Mai Chau Vietnam", "Pu Luong Vietnam", "Ta Xua Vietnam",
    
    # Specific attractions - Ho Chi Minh
    "Ben Thanh Market Ho Chi Minh", "Notre Dame Cathedral Saigon", "War Remnants Museum Ho Chi Minh",
    "Independence Palace Ho Chi Minh", "Saigon Opera House", "Bitexco Tower Ho Chi Minh",
    
    # Specific attractions - Hanoi  
    "Hoan Kiem Lake Hanoi", "Temple of Literature Hanoi", "Old Quarter Hanoi", "Ho Chi Minh Mausoleum",
    "Tran Quoc Pagoda Hanoi", "West Lake Hanoi", "Long Bien Bridge Hanoi",
    
    # Specific attractions - Da Nang
    "Marble Mountains Da Nang", "Ba Na Hills Da Nang", "Golden Bridge Da Nang", "Dragon Bridge Da Nang",
    "My Khe Beach Da Nang", "Lady Buddha Da Nang",
    
    # Specific attractions - Hoi An
    "Japanese Bridge Hoi An", "Old Town Hoi An", "An Bang Beach Hoi An", "Tra Que Village Hoi An",
    
    # Specific attractions - Nha Trang
    "Vinpearl Nha Trang", "Po Nagar Cham Towers Nha Trang", "Long Son Pagoda Nha Trang",
    
    # Nature & Parks
    "Phong Nha Cave Vietnam", "Son Doong Cave Vietnam", "Bach Ma National Park Vietnam",
    "Cuc Phuong National Park Vietnam", "Tam Coc Ninh Binh", "Trang An Ninh Binh",
    
    # Additional cities
    "Quy Nhon Vietnam", "Phan Thiet Vietnam", "Buon Ma Thuot Vietnam", "Pleiku Vietnam",
    "Kon Tum Vietnam", "Ca Mau Vietnam", "Rach Gia Vietnam", "Ha Tien Vietnam",
    
    # Islands & coastal
    "Con Dao Island Vietnam", "Ly Son Island Vietnam", "Quan Lan Island Vietnam",
    "Co To Island Vietnam", "Nam Du Island Vietnam",
    
    # More specific POIs
    "Saigon Central Post Office", "Reunification Palace Ho Chi Minh", "Suoi Tien Park Ho Chi Minh",
    "Dam Sen Park Ho Chi Minh", "Binh Tay Market Ho Chi Minh", "Giac Lam Pagoda Ho Chi Minh",
    "Dong Khoi Street Ho Chi Minh", "Nguyen Hue Walking Street Ho Chi Minh",
    
    "Ba Dinh Square Hanoi", "Dong Xuan Market Hanoi", "Hanoi Opera House", "Vietnam Museum of Ethnology",
    "Thang Long Water Puppet Theatre", "St Joseph Cathedral Hanoi", "Train Street Hanoi",
    
    "Linh Ung Pagoda Da Nang", "Han River Bridge Da Nang", "Asia Park Da Nang", "Sun World Ba Na Hills",
    
    "Coconut Forest Hoi An", "Cam Thanh Village Hoi An", "Cham Island Hoi An",
    
    "Yang Bay Waterfall Nha Trang", "Nha Trang Cathedral", "Dam Market Nha Trang",
    
    # Historical sites
    "Dien Bien Phu Battlefield Vietnam", "DMZ Vietnam", "Vinh Moc Tunnels Vietnam",
    
    # Food & Markets
    "Ben Thanh Night Market", "Dong Ba Market Hue", "Han Market Da Nang", "Cai Rang Floating Market Can Tho",
    
    # Additional beaches & resorts
    "Bai Chay Beach Ha Long", "Tuan Chau Island Ha Long", "Doc Let Beach Nha Trang",
    "Bai Dai Beach Nha Trang", "Ke Ga Beach Phan Thiet", "Bai Xep Beach Quy Nhon",
    
    # Mountain towns
    "Tam Dao Vietnam", "Ba Vi Vietnam", "Da Lat Flower Garden", "Dalat Night Market",
    "Crazy House Dalat", "Datanla Waterfall Dalat", "Langbiang Mountain Dalat",
    
    # Additional cultural sites
    "Thien Mu Pagoda Hue", "Tomb of Khai Dinh Hue", "Tomb of Minh Mang Hue",
    "Perfume Pagoda Hanoi", "Bai Dinh Pagoda Ninh Binh", "Huong Tich Cave Hanoi",
    
    # Adventure & nature
    "Cat Tien National Park Vietnam", "Yok Don National Park Vietnam", "Phu Quoc National Park",
    "Dray Nur Waterfall Vietnam", "Dray Sap Waterfall Vietnam", "Elephant Falls Dalat",
    
    # Additional islands
    "Hon Mun Island Nha Trang", "Hon Tam Island Nha Trang", "Monkey Island Nha Trang",
    "Ngoc Island Phu Quoc", "Fingernail Island Phu Quoc", "May Rut Island Phu Quoc",
    
    # Urban attractions
    "Bitexco Financial Tower", "Landmark 81 Ho Chi Minh", "Lotte Center Hanoi",
    "Vincom Center Da Nang", "Indochina Plaza Hanoi",
    
    # More beaches
    "Non Nuoc Beach Da Nang", "Thanh Binh Beach Da Nang", "Bai Truoc Beach Vung Tau",
    "Bai Sau Beach Vung Tau", "Ham Tien Beach Mui Ne", "Hon Rom Beach Phan Thiet",
]


async def create_user_with_preference(db: AsyncSession, user_data: dict):
    """Helper to create user with preference using services"""
    try:
        # Check if user already exists
        users = await UserRepository.search_users(db, user_data["email"], limit=1)
        if users:
            return None, None
        
        # Create user via repository (direct creation for bulk import without email verification)
        register_data = UserRegister(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"]
        )
        new_user = await UserRepository.create_user(db, register_data)
        if not new_user:
            print(f"  ❌ Failed to create user {user_data.get('username')}")
            return None, None
        
        # Update rank if specified
        if user_data.get("rank") and user_data["rank"] != Rank.bronze:
            from schemas.user_schema import UserUpdateEcoPoint
            # Note: In real scenario, rank should be set by eco_points logic
            new_user.rank = user_data["rank"]
            await db.commit()
            await db.refresh(new_user)
        
        # Create preference
        pref_data = user_data.get("preference", {})
        if pref_data:
            await ClusterRepository.update_preference(
                db,
                user_id=new_user.id,
                weather_pref=pref_data.get("weather_pref"),
                attraction_types=pref_data.get("attraction_types"),
                budget_range=pref_data.get("budget_range"),
                kids_friendly=pref_data.get("kids_friendly", False)
            )
        else:
            # Create empty preference
            await ClusterRepository.create_preference(db, user_id=new_user.id)
        
        preference = await ClusterRepository.get_preference(db, new_user.id)
        
        return new_user, preference
    except Exception as e:
        await db.rollback()
        print(f"  ❌ Failed to create user {user_data.get('username')}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def fetch_destinations_via_autocomplete(db: AsyncSession, sample_size: int = 200) -> list[str]:
    """Fetch real destination Place IDs using autocomplete API"""
    print(f"\n🗺️  Fetching {sample_size} destinations from Vietnam using Google Places API...")
    
    place_ids = []
    seen_ids = set()
    
    # Shuffle locations for variety
    locations = VIETNAM_LOCATIONS.copy()
    random.shuffle(locations)
    
    # Generate a session token for the autocomplete requests
    import uuid
    session_token = str(uuid.uuid4())
    
    for query in locations:
        if len(place_ids) >= sample_size:
            break
            
        try:
            request = AutocompleteRequest(query=query, session_token=session_token)
            response = await MapService.autocomplete(db, request)
            
            if response and response.predictions:
                for prediction in response.predictions[:3]:  # Take up to 3 from each search
                    place_id = prediction.place_id
                    if place_id not in seen_ids:
                        place_ids.append(place_id)
                        seen_ids.add(place_id)
                        print(f"  ✅ [{len(place_ids)}] {prediction.description}")
                        
                    if len(place_ids) >= sample_size:
                        break
        except Exception as e:
            print(f"  ⚠️ Failed to fetch '{query}': {e}")
            continue
    
    print(f"\n📍 Successfully collected {len(place_ids)} unique destinations\n")
    return place_ids


async def create_destinations_with_embeddings(db: AsyncSession, place_ids: list[str]) -> int:
    """Create destination records with embeddings using services"""
    print(f"🏗️  Creating {len(place_ids)} destination records with embeddings...")
    
    created_count = 0
    for idx, place_id in enumerate(place_ids, 1):
        try:
            # Check if destination already exists
            existing = await DestinationService.get_destination_by_id(db, place_id)
            if existing:
                continue
        except:
            # Destination doesn't exist, create it
            pass
        
        try:
            # Create destination using service
            dest_data = DestinationCreate(place_id=place_id)
            await DestinationService.create_destination(db, dest_data)
            
            # Generate and save embedding using service
            destination_metadata = {
                "name": f"Tourist destination in Vietnam",
                "tags": ["tourist_attraction", "place_to_visit", "vietnam"],
                "category": "tourist_attraction"
            }
            
            embedding = await DestinationService.embed_destination_by_id(
                db, place_id, destination_metadata
            )
            
            if embedding:
                created_count += 1
                
            if idx % 20 == 0:
                print(f"  ⏳ Progress: {idx}/{len(place_ids)} destinations processed")
        
        except Exception as e:
            print(f"  ⚠️ Failed to create destination {place_id}: {e}")
            continue
    
    print(f"✅ Created {created_count} destinations with embeddings\n")
    return created_count


async def create_user_activities(db: AsyncSession, user_ids: list[int], place_ids: list[str]) -> int:
    """Create random user activities for destinations using services"""
    print(f"👥 Creating user activities for {len(user_ids)} users across {len(place_ids)} destinations...")
    
    activity_count = 0
    for user_id in user_ids:
        # Each user interacts with 5-15 random destinations
        num_interactions = random.randint(5, 15)
        user_destinations = random.sample(place_ids, min(num_interactions, len(place_ids)))
        
        for place_id in user_destinations:
            try:
                # Use UserService to log activities
                activity_data = UserActivityCreate(
                    activity=random.choice([Activity.search_destination, Activity.save_destination]),
                    destination_id=place_id
                )
                await UserService.log_user_activity(db, user_id, activity_data)
                activity_count += 1
            except Exception as e:
                # Silently continue if activity creation fails (could be duplicate or other issue)
                continue
    
    print(f"✅ Created {activity_count} user activities\n")
    return activity_count


async def bulk_create_users(db: AsyncSession) -> tuple[int, int]:
    """Main bulk creation function"""
    print("\n" + "=" * 70)
    print("🚀 BULK DATA CREATION - VIETNAM DESTINATIONS")
    print("=" * 70)
    
    try:
        # Step 1: Create users (or use existing users 1-62)
        print("\n📋 Step 1: Checking/Creating users...")
        user_ids = list(range(1, 62))  # Use users 1-61
        created_users = 0
        created_preferences = 0
        
        for user_data in SAMPLE_USERS:
            user, pref = await create_user_with_preference(db, user_data)
            if user:
                created_users += 1
                print(f"  ✅ Created user: {user.username} (ID: {user.id})")
            if pref:
                created_preferences += 1
        
        print(f"\n✅ Total users available: {len(user_ids)}")
        print(f"   New users created: {created_users}")
        print(f"   Preferences created: {created_preferences}\n")
        
        # Step 2: Fetch ~200 destinations via autocomplete
        print("\n📋 Step 2: Fetching destinations...")
        place_ids = await fetch_destinations_via_autocomplete(db, sample_size=200)
        
        if not place_ids:
            print("❌ No destinations fetched. Aborting.")
            return created_users, created_preferences
        
        # Step 3: Create destination records with embeddings
        print("\n📋 Step 3: Creating destination records...")
        destinations_created = await create_destinations_with_embeddings(db, place_ids)
        
        # Step 4: Create user activities
        print("\n📋 Step 4: Creating user activities...")
        activities_created = await create_user_activities(db, user_ids, place_ids)
        
        # Step 5: Run clustering to assign users to clusters
        print("\n📋 Step 5: Running clustering algorithm...")
        try:
            clustering_result = await ClusterService.run_user_clustering(db)
            print(f"  ✅ Clustering completed:")
            print(f"     - Users clustered: {clustering_result.stats.users_clustered}")
            print(f"     - Clusters updated: {clustering_result.stats.clusters_updated}")
            print(f"     - Embeddings generated: {clustering_result.stats.embeddings_generated}")
        except Exception as cluster_error:
            print(f"  ⚠️ Clustering failed: {cluster_error}")
        
        # Final summary
        print("\n" + "=" * 70)
        print("📊 BULK CREATION SUMMARY")
        print("=" * 70)
        print(f"   👥 Users: {len(user_ids)} total ({created_users} new)")
        print(f"   🗂️  Preferences: {created_preferences} created")
        print(f"   📍 Destinations: {destinations_created} created")
        print(f"   🔢 Place IDs collected: {len(place_ids)}")
        print(f"   📝 User Activities: {activities_created} created")
        print("=" * 70 + "\n")
        
        return created_users, created_preferences
        
    except Exception as e:
        await db.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e


# Allow running this script directly
if __name__ == "__main__":
    import asyncio
    from database.db import UserAsyncSessionLocal
    from database.init_database import init_db
    
    async def main():
        """Main entry point for direct execution"""
        print("\n🚀 Starting bulk data creation script...")
        
        # Initialize database first
        try:
            await init_db(drop_all=False)
            print("✅ Database initialized\n")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return
        
        # Run bulk creation
        async with UserAsyncSessionLocal() as db:
            try:
                created_users, created_preferences = await bulk_create_users(db)
                print(f"\n✅ Script completed successfully!")
                print(f"   Created {created_users} users with {created_preferences} preferences")
            except Exception as e:
                print(f"\n❌ Script failed: {e}")
                raise
    
    # Run the async main function
    asyncio.run(main())
