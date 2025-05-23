"""
Memory management API endpoints for Core Conversational Engine.
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import verify_token, verify_scope, TokenData
from app.memory.persistence import MemoryPersistence
from app.memory.vector_db import VectorDBFactory

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/memory", tags=["memory"])

# Models for request/response
class KnowledgeRequest(BaseModel):
    """Request model for adding knowledge."""
    text: str
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeResponse(BaseModel):
    """Response model for knowledge."""
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeSearchRequest(BaseModel):
    """Request model for searching knowledge."""
    query: str
    limit: Optional[int] = 5
    filter: Optional[Dict[str, Any]] = None


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge search results."""
    results: List[Dict[str, Any]]


class EpisodicMemoryRequest(BaseModel):
    """Request model for adding episodic memory."""
    memory_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class EpisodicMemoryResponse(BaseModel):
    """Response model for episodic memory."""
    memory_id: str
    memory_type: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class EpisodicMemorySearchRequest(BaseModel):
    """Request model for searching episodic memory."""
    query: str
    memory_type: Optional[str] = None
    limit: Optional[int] = 5


class EpisodicMemorySearchResponse(BaseModel):
    """Response model for episodic memory search results."""
    results: List[Dict[str, Any]]


# Dependency for getting components
async def get_memory_persistence():
    """Get memory persistence instance."""
    # In a real implementation, this would be a singleton or dependency injection
    persistence = MemoryPersistence()
    await persistence.initialize()
    return persistence


# Endpoints
@router.post("/knowledge", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def add_knowledge(
    knowledge_request: KnowledgeRequest,
    token_data: TokenData = Depends(verify_scope("memory:write")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Add knowledge to the knowledge base.
    """
    try:
        # Add metadata
        metadata = knowledge_request.metadata or {}
        metadata["user_id"] = token_data.sub
        
        # Add to knowledge base
        ids = await persistence.add_to_knowledge_base(
            texts=[knowledge_request.text],
            metadata=[metadata]
        )
        
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add knowledge"
            )
        
        # Return response
        return {
            "id": ids[0],
            "text": knowledge_request.text,
            "metadata": metadata
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding knowledge: {str(e)}"
        )


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    token_data: TokenData = Depends(verify_scope("memory:read")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Search the knowledge base.
    """
    try:
        # Search knowledge base
        results = await persistence.search_knowledge_base(
            query=search_request.query,
            limit=search_request.limit,
            filter=search_request.filter
        )
        
        # Return response
        return {
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge: {str(e)}"
        )


@router.post("/episodic", response_model=EpisodicMemoryResponse, status_code=status.HTTP_201_CREATED)
async def add_episodic_memory(
    memory_request: EpisodicMemoryRequest,
    token_data: TokenData = Depends(verify_scope("memory:write")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Add episodic memory.
    """
    try:
        # Add metadata
        metadata = memory_request.metadata or {}
        metadata["source"] = "api"
        
        # Add episodic memory
        memory_id = await persistence.add_episodic_memory(
            user_id=token_data.sub,
            memory_type=memory_request.memory_type,
            content=memory_request.content,
            metadata=metadata
        )
        
        if not memory_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add episodic memory"
            )
        
        # Return response
        return {
            "memory_id": memory_id,
            "memory_type": memory_request.memory_type,
            "content": memory_request.content,
            "timestamp": metadata.get("timestamp", ""),
            "metadata": metadata
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding episodic memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding episodic memory: {str(e)}"
        )


@router.post("/episodic/search", response_model=EpisodicMemorySearchResponse)
async def search_episodic_memory(
    search_request: EpisodicMemorySearchRequest,
    token_data: TokenData = Depends(verify_scope("memory:read")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Search episodic memory.
    """
    try:
        # Search episodic memory
        results = await persistence.search_episodic_memory(
            user_id=token_data.sub,
            query=search_request.query,
            memory_type=search_request.memory_type,
            limit=search_request.limit
        )
        
        # Return response
        return {
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error searching episodic memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching episodic memory: {str(e)}"
        )
