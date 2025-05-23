"""
Conversation API endpoints for Core Conversational Engine.
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.api.auth import verify_token, verify_scope, TokenData
from app.memory.conversation import Conversation, Message
from app.memory.persistence import MemoryPersistence
from app.memory.retrieval import ContextRetrieval
from app.models.router import ModelRouter

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/conversation", tags=["conversation"])

# Models for request/response
class MessageRequest(BaseModel):
    """Request model for sending a message."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    message_id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    conversation_id: str
    title: str
    messages: List[MessageResponse]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""
    conversations: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


# Dependency for getting components
async def get_memory_persistence():
    """Get memory persistence instance."""
    # In a real implementation, this would be a singleton or dependency injection
    persistence = MemoryPersistence()
    await persistence.initialize()
    return persistence


async def get_context_retrieval(persistence=Depends(get_memory_persistence)):
    """Get context retrieval instance."""
    return ContextRetrieval(persistence)


async def get_model_router():
    """Get model router instance."""
    # In a real implementation, this would be a singleton or dependency injection
    return ModelRouter()


# Endpoints
@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    token_data: TokenData = Depends(verify_scope("conversation:write")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Create a new conversation.
    """
    try:
        # Create conversation
        conversation = Conversation(
            title=f"New Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            metadata={"user_id": token_data.sub}
        )
        
        # Save conversation
        success = await persistence.save_conversation(conversation)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation"
            )
        
        # Format response
        return {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "messages": [
                {
                    "message_id": message.message_id,
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata
                }
                for message in conversation.messages
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "metadata": conversation.metadata
        }
    
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    token_data: TokenData = Depends(verify_scope("conversation:read")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Get a conversation by ID.
    """
    try:
        # Load conversation
        conversation = await persistence.load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Check ownership (in a real system, would check against user ID)
        # For simplicity, we're not implementing this check here
        
        # Format response
        return {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "messages": [
                {
                    "message_id": message.message_id,
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata
                }
                for message in conversation.messages
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "metadata": conversation.metadata
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting conversation: {str(e)}"
        )


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_request: MessageRequest,
    token_data: TokenData = Depends(verify_scope("conversation:write")),
    persistence: MemoryPersistence = Depends(get_memory_persistence),
    context_retrieval: ContextRetrieval = Depends(get_context_retrieval),
    model_router: ModelRouter = Depends(get_model_router)
):
    """
    Send a message to a conversation and get a response.
    """
    try:
        # Load conversation
        conversation = await persistence.load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Create user message
        user_message = Message(
            role="user",
            content=message_request.content,
            metadata=message_request.metadata or {}
        )
        
        # Add message to conversation
        conversation.add_message(user_message)
        
        # Get context
        context = await context_retrieval.get_combined_context(
            conversation_id=conversation_id,
            user_id=token_data.sub,
            query=message_request.content
        )
        
        # Generate prompt with context
        prompt = f"""
        Conversation History:
        {context['conversation_history']}
        
        {context['user_context']}
        
        {context['knowledge_context']}
        
        User: {message_request.content}
        
        Assistant:
        """
        
        # Generate response
        response_text = await model_router.generate(prompt)
        
        # Create assistant message
        assistant_message = Message(
            role="assistant",
            content=response_text,
            metadata={"model": model_router._primary_model.model_name}
        )
        
        # Add message to conversation
        conversation.add_message(assistant_message)
        
        # Save conversation
        await persistence.save_conversation(conversation)
        
        # Extract and save learnings
        learnings = await context_retrieval.extract_learning(conversation, token_data.sub)
        if learnings:
            await context_retrieval.save_learnings(learnings)
        
        # Return assistant message
        return {
            "message_id": assistant_message.message_id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "timestamp": assistant_message.timestamp.isoformat(),
            "metadata": assistant_message.metadata
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    page_size: int = 10,
    token_data: TokenData = Depends(verify_scope("conversation:read")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    List conversations for the current user.
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get conversations
        conversations = await persistence.list_conversations(limit=page_size, offset=offset)
        
        # In a real system, would filter by user ID
        # For simplicity, we're not implementing this filter here
        
        # Return response
        return {
            "conversations": conversations,
            "total": len(conversations),  # In a real system, would get total count
            "page": page,
            "page_size": page_size
        }
    
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing conversations: {str(e)}"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    token_data: TokenData = Depends(verify_scope("conversation:write")),
    persistence: MemoryPersistence = Depends(get_memory_persistence)
):
    """
    Delete a conversation.
    """
    try:
        # Check if conversation exists
        conversation = await persistence.load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # In a real system, would check ownership
        # For simplicity, we're not implementing this check here
        
        # Delete conversation
        success = await persistence.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete conversation {conversation_id}"
            )
        
        # Return no content
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation: {str(e)}"
        )


# WebSocket endpoint for streaming conversation
@router.websocket("/ws/{conversation_id}")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: str,
    persistence: MemoryPersistence = Depends(get_memory_persistence),
    context_retrieval: ContextRetrieval = Depends(get_context_retrieval),
    model_router: ModelRouter = Depends(get_model_router)
):
    """
    WebSocket endpoint for streaming conversation.
    """
    await websocket.accept()
    
    try:
        # Load conversation
        conversation = await persistence.load_conversation(conversation_id)
        if not conversation:
            await websocket.send_json({"error": f"Conversation {conversation_id} not found"})
            await websocket.close()
            return
        
        # Main WebSocket loop
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Process message
            if "message" in data:
                user_message_content = data["message"]
                user_id = data.get("user_id", "anonymous")
                
                # Create user message
                user_message = Message(
                    role="user",
                    content=user_message_content,
                    metadata={"source": "websocket"}
                )
                
                # Add message to conversation
                conversation.add_message(user_message)
                
                # Get context
                context = await context_retrieval.get_combined_context(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    query=user_message_content
                )
                
                # Generate prompt with context
                prompt = f"""
                Conversation History:
                {context['conversation_history']}
                
                {context['user_context']}
                
                {context['knowledge_context']}
                
                User: {user_message_content}
                
                Assistant:
                """
                
                # Send initial response
                await websocket.send_json({
                    "type": "start",
                    "message_id": str(uuid.uuid4())
                })
                
                # Generate streaming response
                full_response = ""
                async for chunk in model_router.generate_stream(prompt):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Create assistant message
                assistant_message = Message(
                    role="assistant",
                    content=full_response,
                    metadata={"model": model_router._primary_model.model_name, "source": "websocket"}
                )
                
                # Add message to conversation
                conversation.add_message(assistant_message)
                
                # Save conversation
                await persistence.save_conversation(conversation)
                
                # Send completion
                await websocket.send_json({
                    "type": "end",
                    "message_id": assistant_message.message_id
                })
                
                # Extract and save learnings
                learnings = await context_retrieval.extract_learning(conversation, user_id)
                if learnings:
                    await context_retrieval.save_learnings(learnings)
            
            elif "ping" in data:
                # Handle ping
                await websocket.send_json({"type": "pong"})
            
            else:
                # Handle unknown message type
                await websocket.send_json({"type": "error", "message": "Unknown message type"})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for conversation {conversation_id}: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except:
            pass
