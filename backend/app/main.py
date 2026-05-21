"""
Wallora - AI-Powered Art Discovery Platform
Run: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine
from app.models.models import Base
from app.api import auth, artworks, collections, search, admin
from app.services.model_manager import model_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Load AI models
    logger.info("Starting Wallora API...")
    try:
        model_manager.load_models()
        logger.info("AI models loaded and cached in VRAM")
    except Exception as e:
        logger.error(f"Failed to load some models: {e}")
        logger.warning("API will start but some AI features may be unavailable")
    
    yield
    
    # Shutdown: Clean up
    logger.info("Shutting down...")
    model_manager.unload_models()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Powered Art Discovery & Marketplace",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(artworks.router)
app.include_router(collections.router)
app.include_router(search.router)
app.include_router(admin.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "models_loaded": model_manager.is_loaded(),
        "device": model_manager.device
    }

@app.get("/models/status")
async def model_status():
    """Check which models are loaded"""
    return {
        "device": model_manager.device,
        "models_loaded": model_manager.is_loaded(),
        "available_models": {
            name: model is not None 
            for name, model in model_manager.models.items()
        },
        "vram_usage": f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB" 
        if torch.cuda.is_available() else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    import torch
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)