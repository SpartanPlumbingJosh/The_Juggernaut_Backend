"""
Core Engine Main Module

This module initializes and provides the core engine functionality.
It integrates with Ollama for text, image, and video generation.
"""

import os
import logging
from typing import Dict, Any, Optional, List

# Import Ollama integration
from ollama_integration import OllamaModelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store conversation histories
conversation_histories = {}

def initialize_engine() -> Dict[str, Any]:
    """
    Initialize the core engine with Ollama integration.
    
    Returns:
        Dict: Engine components and configuration
    """
    logger.info("Initializing core engine with Ollama integration")
    
    # Initialize Ollama model manager
    ollama_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
    model_manager = OllamaModelManager(base_url=ollama_url)
    
    # Initialize engine components
    engine = {
        "model_manager": model_manager,
        "config": {
            "use_ollama": True,
            "supports_multimodal": True
        }
    }
    
    logger.info("Core engine initialized successfully")
    return engine

def process_text_request(engine: Dict[str, Any], prompt: str, session_id: str = "", model: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a text generation request with conversation history.
    
    Args:
        engine: Engine components and configuration
        prompt: Text prompt
        session_id: Session identifier for conversation context
        model: Optional specific model to use
        
    Returns:
        Dict: Response with generated text
    """
    model_manager = engine["model_manager"]
    
    # Get or initialize conversation history
    if session_id not in conversation_histories:
        conversation_histories[session_id] = [
            {"role": "system", "content": "You are the Juggernaut Elite Manus AI assistant."}
        ]
    
    # Add user message to history
    conversation_histories[session_id].append({"role": "user", "content": prompt})
    
    # Use chat endpoint with history
    response = model_manager.chat_with_history(
        conversation_histories[session_id],
        model
    )
    
    # Add assistant response to history
    if "message" in response:
        assistant_message = response["message"]["content"]
        conversation_histories[session_id].append(
            {"role": "assistant", "content": assistant_message}
        )
        return {"response": assistant_message}
    else:
        # Fallback to generate_text if chat fails
        logger.warning("Chat with history failed, falling back to generate_text")
        fallback_response = model_manager.generate_text(prompt, model)
        return fallback_response

def process_image_request(engine: Dict[str, Any], prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Process an image generation request.
    
    Args:
        engine: Engine components and configuration
        prompt: Image description
        model: Optional specific model to use
        
    Returns:
        Dict: Response with generated image
    """
    model_manager = engine["model_manager"]
    response = model_manager.generate_image(prompt, model)
    return response

def process_video_request(engine: Dict[str, Any], prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a video generation request.
    
    Args:
        engine: Engine components and configuration
        prompt: Video description
        model: Optional specific model to use
        
    Returns:
        Dict: Response with generated video
    """
    model_manager = engine["model_manager"]
    response = model_manager.generate_video(prompt, model)
    return response

def get_available_models(engine: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a list of all available models.
    
    Args:
        engine: Engine components and configuration
        
    Returns:
        Dict: Dictionary of available models by type
    """
    model_manager = engine["model_manager"]
    return model_manager.get_available_models()

def clear_conversation_history(session_id: str) -> bool:
    """
    Clear the conversation history for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    if session_id in conversation_histories:
        conversation_histories[session_id] = [
            {"role": "system", "content": "You are the Juggernaut Elite Manus AI assistant."}
        ]
        return True
    return False
