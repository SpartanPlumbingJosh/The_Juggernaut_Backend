"""
Main application entry point for Core Conversational Engine.
Includes router registration and API setup.
"""
import logging
from fastapi import FastAPI

from app.api.main import app
from app.api.conversation import router as conversation_router
from app.api.memory import router as memory_router
from app.api.config import router as config_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Register routers
app.include_router(conversation_router)
app.include_router(memory_router)
app.include_router(config_router)

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Core Conversational Engine")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
