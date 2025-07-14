"""
FastAPI main application
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from .routers import products, brands, analytics
from ..database.connection import init_database
from ..config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Initialize database on startup
    init_database()
    yield
    # Cleanup resources on shutdown


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-site product price tracking system API",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(brands.router, prefix="/api/v1/brands", tags=["brands"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/")
async def root():
    """Root route"""
    return {
        "message": "Welcome to Price Cage API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "price_cage_api"}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 error handler"""
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 error handler"""
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers
    )