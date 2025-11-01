from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import all routers
from routers.authentication_router import router as auth_router
from routers.user_router import router as user_router
from routers.review_router import router as review_router
from routers.carbon_router import router as carbon_router
# from routers.chatbot_router import router as chatbot_router
# from routers.recommendation_router import router as recommendation_router
from routers.reward_router import router as reward_router

# Import database setup
from database.database import engine
from models.init_database import init_db
from utils.config import settings

# Lifespan event handler (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables
    print("🚀 Starting EcomoveX Backend...")
    await init_db(drop_all=False)
    print("✅ Database initialized")
    
    yield  # App is running
    
    # Shutdown: Cleanup
    print("🛑 Shutting down EcomoveX Backend...")
    await engine.dispose()
    print("✅ Database connections closed")


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
app.include_router(carbon_router)
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