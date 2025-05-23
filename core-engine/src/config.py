"""
Configuration API endpoints for Core Conversational Engine.
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import verify_token, verify_scope, TokenData

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/config", tags=["config"])

# Models for request/response
class ModelConfigRequest(BaseModel):
    """Request model for updating model configuration."""
    primary_model: Optional[str] = None
    fallback_models: Optional[List[str]] = None
    complexity_threshold: Optional[int] = None
    token_threshold: Optional[int] = None


class ModelConfigResponse(BaseModel):
    """Response model for model configuration."""
    primary_model: str
    fallback_models: List[str]
    complexity_threshold: int
    token_threshold: int


class VectorDBConfigRequest(BaseModel):
    """Request model for updating vector database configuration."""
    db_type: str  # "pinecone" or "chromadb"
    api_key: Optional[str] = None
    environment: Optional[str] = None
    dimension: Optional[int] = None
    persist_directory: Optional[str] = None


class VectorDBConfigResponse(BaseModel):
    """Response model for vector database configuration."""
    db_type: str
    status: str
    collections: List[str]


class SystemConfigResponse(BaseModel):
    """Response model for system configuration."""
    version: str
    environment: str
    models_available: List[str]
    vector_db_type: str
    memory_enabled: bool


# Mock configuration (in a real system, would use a configuration service)
_model_config = {
    "primary_model": "gpt-4",
    "fallback_models": ["gpt-3.5-turbo", "llama-2-7b"],
    "complexity_threshold": 7,
    "token_threshold": 2000
}

_vector_db_config = {
    "db_type": "chromadb",
    "status": "connected",
    "collections": ["knowledge", "episodic_memory"]
}

_system_config = {
    "version": "1.0.0",
    "environment": "development",
    "models_available": ["gpt-4", "gpt-3.5-turbo", "llama-2-7b", "mistral-7b"],
    "vector_db_type": "chromadb",
    "memory_enabled": True
}


# Endpoints
@router.get("/model", response_model=ModelConfigResponse)
async def get_model_config(
    token_data: TokenData = Depends(verify_scope("config:read"))
):
    """
    Get model configuration.
    """
    try:
        return _model_config
    except Exception as e:
        logger.error(f"Error getting model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model configuration: {str(e)}"
        )


@router.put("/model", response_model=ModelConfigResponse)
async def update_model_config(
    config_request: ModelConfigRequest,
    token_data: TokenData = Depends(verify_scope("config:write"))
):
    """
    Update model configuration.
    """
    try:
        # Update configuration
        if config_request.primary_model is not None:
            _model_config["primary_model"] = config_request.primary_model
        
        if config_request.fallback_models is not None:
            _model_config["fallback_models"] = config_request.fallback_models
        
        if config_request.complexity_threshold is not None:
            _model_config["complexity_threshold"] = config_request.complexity_threshold
        
        if config_request.token_threshold is not None:
            _model_config["token_threshold"] = config_request.token_threshold
        
        # Return updated configuration
        return _model_config
    except Exception as e:
        logger.error(f"Error updating model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating model configuration: {str(e)}"
        )


@router.get("/vector-db", response_model=VectorDBConfigResponse)
async def get_vector_db_config(
    token_data: TokenData = Depends(verify_scope("config:read"))
):
    """
    Get vector database configuration.
    """
    try:
        return _vector_db_config
    except Exception as e:
        logger.error(f"Error getting vector database configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting vector database configuration: {str(e)}"
        )


@router.put("/vector-db", response_model=VectorDBConfigResponse)
async def update_vector_db_config(
    config_request: VectorDBConfigRequest,
    token_data: TokenData = Depends(verify_scope("config:write"))
):
    """
    Update vector database configuration.
    """
    try:
        # Update configuration
        _vector_db_config["db_type"] = config_request.db_type
        
        # In a real implementation, would update the vector database client
        # For this example, we'll just update the mock configuration
        
        # Return updated configuration
        return _vector_db_config
    except Exception as e:
        logger.error(f"Error updating vector database configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vector database configuration: {str(e)}"
        )


@router.get("/system", response_model=SystemConfigResponse)
async def get_system_config(
    token_data: TokenData = Depends(verify_scope("config:read"))
):
    """
    Get system configuration.
    """
    try:
        return _system_config
    except Exception as e:
        logger.error(f"Error getting system configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system configuration: {str(e)}"
        )
