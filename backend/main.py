from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.db import get_sync_session
from utils.embedded.faiss_utils import build_index

# Import database setup
from database.db import engine
from database.db import UserAsyncSessionLocal
from database.init_database import init_db
from database.create_all_databases import create_databases
from scripts import bulk_create
from routers.air_router import router as air_router
from routers.authentication_router import router as auth_router
from routers.chatbot_router import router as chatbot_router
from routers.destination_router import router as destination_router
from routers.friend_router import router as friend_router
from routers.green_verification_router import router as green_verification_router
from routers.map_router import router as map_router
from routers.message_router import router as message_router
from routers.review_router import router as review_router
from routers.reward_router import router as reward_router
from routers.room_router import router as room_router
from routers.route_router import router as route_router
from routers.storage_router import router as storage_router
from routers.plan_router import router as plan_router
from routers.recommendation_router import router as recommendation_router
from routers.cluster_router import router as cluster_router
from routers.user_router import router as user_router
from routers.weather_router import router as weather_router
from routers.carbon_router import router as carbon_router
from utils.config import settings
from services.cluster_service import ClusterService

# Scheduler instance
scheduler = AsyncIOScheduler()

# Background clustering job
async def scheduled_clustering_job():
    """
    Background job to re-cluster all users every 7 days.
    This updates cluster assignments based on latest preferences and activities.
    """
    try:
        async for db in UserAsyncSessionLocal():
            result = await ClusterService.run_user_clustering(db)
            
            if result.success:
                print("\n✅ Scheduled clustering completed successfully!")
                print(f"📊 Stats: {result.stats.users_clustered} users in {result.stats.clusters_updated} clusters")
            else:
                print(f"\n❌ Scheduled clustering failed: {result.message}")
            
            break  # Exit after first session
            
    except Exception as e:
        print(f"\n❌ Error in scheduled clustering job: {e}")


# Lifespan event handler (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    CREATE_DATABASE = False
    if CREATE_DATABASE:
        try:
            await create_databases()
            print("Database created and initialized")
        except Exception as e:
            print(f"WARNING: Database creation failed - {e}")
    else:
        print("Database creation skipped")

    # Startup
    print("Starting EcomoveX ..")

    try:
        await init_db(drop_all=False)
        print("Database initialized")
    except Exception as e:
        print(f"WARNING: Database initialization failed - {e}")

    RUN_BULK_CREATE_USERS = False

    if RUN_BULK_CREATE_USERS:
        try:
            async with UserAsyncSessionLocal() as db:
                print("📝 Creating sample users...")
                await bulk_create.bulk_create_users(db=db)
                print("✅ Sample users created successfully")
        except Exception as e:
            print(f"WARNING: Bulk create users failed - {e}")
    else:
        print("ℹ️  Bulk create users is disabled")

    # Initialize FAISS index for recommendations
    try:
        print("🔧 Initializing FAISS recommendation index...")
        with get_sync_session() as db:
            success = build_index(db, normalize=False)
            if success:
                print("✅ FAISS index built successfully")
            else:
                print("⚠️ FAISS index build failed - recommendations may be limited")
    except Exception as e:
        print(f"⚠️ WARNING: FAISS index initialization failed - {e}")
        print("   Recommendations will fall back to database-only queries")

    # Start APScheduler for periodic clustering
    try:
        print("⏰ Starting scheduler for automated clustering...")
        scheduler.add_job(
            scheduled_clustering_job,
            trigger=IntervalTrigger(days=7),  # Run every 7 days
            id="clustering_job",
            name="Re-cluster all users",
            replace_existing=True,
            max_instances=1  # Only one instance at a time
        )
        scheduler.start()
        print("✅ Scheduler started - clustering will run every 7 days")
        print("   Next run: Check scheduler logs")
    except Exception as e:
        print(f"⚠️ WARNING: Scheduler initialization failed - {e}")
        print("   Automated clustering will not be available")

    yield  # App is running

    # Shutdown: Cleanup
    print("Shutting down EcomoveX ..")

    # Stop scheduler
    try:
        scheduler.shutdown(wait=False)
        print("Scheduler stopped")
    except Exception as e:
        print(f"WARNING: Failed to stop scheduler - {e}")

    try:
        await engine.dispose()
        print("Database connections closed")
    except Exception as e:
        print(f"ERROR: Failed to close database - {e}")


# Create FastAPI application
app = FastAPI(
    title="EcomoveX API",
    description="Sustainable Travel & Eco-Mobility Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",  # ReDoc at http://localhost:8000/redoc
)


# CORS Middleware (for frontend communication)
allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
print(f"🌐 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # From local.env
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Include all routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(cluster_router)
app.include_router(review_router)
app.include_router(friend_router)
app.include_router(destination_router)
app.include_router(storage_router)
app.include_router(map_router)
app.include_router(green_verification_router)
app.include_router(air_router)
app.include_router(weather_router)
app.include_router(route_router)
app.include_router(reward_router)
app.include_router(room_router)
app.include_router(message_router)
app.include_router(plan_router)
app.include_router(chatbot_router)
app.include_router(carbon_router)
app.include_router(recommendation_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to EcomoveX API",
        "version": "1.0.0",
        "status": "running",
    }


# Health check endpoint
@app.get("/health", tags=["Root"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# Global exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    print("❌ Validation Error:")
    print(f"   URL: {request.url}")
    print(f"   Method: {request.method}")
    print(f"   Errors: {errors}")

    # Try to get body
    try:
        body = await request.body()
        print(f"   Body: {body.decode()}")
    except:
        pass

    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Run with: uvicorn main:app --reload
