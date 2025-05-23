"""
Core Engine Main Module

This module initializes and provides the core engine functionality.
It integrates with Ollama for text, image, and video generation.
"""

import os
import logging
from typing import Dict, Any, Optional

# Import Ollama integration
from ollama_integration import OllamaModelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def process_text_request(engine: Dict[str, Any], prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a text generation request.
    
    Args:
        engine: Engine components and configuration
        prompt: Text prompt
        model: Optional specific model to use
        
    Returns:
        Dict: Response with generated text
    """
    model_manager = engine["model_manager"]
    response = model_manager.generate_text(prompt, model)
    return response

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
