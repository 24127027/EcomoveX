from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    authentication_router,
    user_router,
    review_router,
    reward_router,
    carbon_router
)

app = FastAPI(
    title="EcomoveX API",
    description="Sustainable Travel Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentication_router.router)
app.include_router(user_router.router)
app.include_router(review_router.router)
app.include_router(reward_router.router)
app.include_router(carbon_router.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to EcomoveX API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
