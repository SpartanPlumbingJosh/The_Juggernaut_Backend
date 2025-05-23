from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import settings
from routes import api_router
from middleware.auth import auth_middleware

app = FastAPI(
    title="Manus AI Assistant API",
    description="API Gateway for the Elite Manus-type AI Assistant",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Add custom middleware
app.middleware("http")(auth_middleware)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Manus AI Assistant API Gateway",
        "documentation": "/docs",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
