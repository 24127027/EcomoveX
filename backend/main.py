from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers.authentication_router import router as auth_router
from routers.user_router import router as user_router
from routers.review_router import router as review_router
from routers.friend_router import router as friend_router
from routers.destination_router import router as destination_router
from routers.storage_router import router as storage_router
# from routers.route_router import router as route_router
# from routers.map_router import router as map_search_router
# from routers.chatbot_router import router as chatbot_router
# from routers.recommendation_router import router as recommendation_router
from routers.reward_router import router as reward_router

# Import database setup
from database.user_database import user_engine
from database.destination_database import destination_engine
from backend.database.init_database import init_user_db, init_destination_db
from utils.config import settings

# Lifespan event handler (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting EcomoveX Backend...")
    
    try:
        await init_user_db(drop_all=False)
        print("User database initialized")
    except Exception as e:
        print(f"WARNING: User database initialization failed - {e}")
    
    try:
        await init_destination_db(drop_all=False)
        print("Destination database initialized")
    except Exception as e:
        print(f"WARNING: Destination database initialization failed - {e}")
    
    # Refresh emission factors from Climatiq API    
    yield  # App is running
    
    # Shutdown: Cleanup
    print("Shutting down EcomoveX Backend...")
    
    try:
        await user_engine.dispose()
        print("User database connections closed")
    except Exception as e:
        print(f"ERROR: Failed to close user database - {e}")
    
    try:
        await destination_engine.dispose()
        print("Destination database connections closed")
    except Exception as e:
        print(f"ERROR: Failed to close destination database - {e}")


# Create FastAPI application
app = FastAPI(
    title="EcomoveX API",
    description="Sustainable Travel & Eco-Mobility Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",           # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",         # ReDoc at http://localhost:8000/redoc
)


# CORS Middleware (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),  # From local.env
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Include all routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(review_router)
app.include_router(friend_router)
app.include_router(destination_router)
app.include_router(storage_router)
# app.include_router(route_router)
# app.include_router(map_search_router)
#app.include_router(chatbot_router)
#app.include_router(recommendation_router)
app.include_router(reward_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return a 204 No Content response to suppress the error
    from fastapi.responses import Response
    return Response(status_code=204)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to EcomoveX API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }


# Run with: uvicorn main:app --reload 