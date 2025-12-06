from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Import database setup
from database.db import engine
from database.init_database import init_db
from routers.air_router import router as air_router
from routers.authentication_router import router as auth_router
from routers.chatbot_router import router as chatbot_router
from routers.destination_router import router as destination_router
from routers.friend_router import router as friend_router
from routers.map_router import router as map_router
from routers.message_router import router as message_router
from routers.review_router import router as review_router
from routers.reward_router import router as reward_router
from routers.room_router import router as room_router
from routers.route_router import router as route_router
from routers.storage_router import router as storage_router
from routers.plan_router import router as plan_router
from routers.recommendation_router import router as recommendation_router

from routers.user_router import router as user_router
from routers.weather_router import router as weather_router
from routers.carbon_router import router as carbon_router
from utils.config import settings


# Lifespan event handler (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting EcomoveX ..")

    try:
        await init_db(drop_all=False)
        print("Database initialized")
    except Exception as e:
        print(f"WARNING: Database initialization failed - {e}")

    # Refresh emission factors from carbonAPI API
    yield  # App is running

    # Shutdown: Cleanup
    print("Shutting down EcomoveX ..")

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
app.include_router(map_router)
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
    # Return a 204 No Content response to suppress the error
    from fastapi.responses import Response

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
    print(f"❌ Validation Error:")
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
