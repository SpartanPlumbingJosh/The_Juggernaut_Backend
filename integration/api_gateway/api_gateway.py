"""
API Gateway Class for Flask Integration

This module provides a Flask-compatible API Gateway class for the Elite Manus AI system.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIGateway:
    """
    API Gateway for the Elite Manus AI system.
    Provides a unified interface for text, image, and video generation.
    """
    
    def __init__(self, engine: Dict[str, Any]):
        """
        Initialize the API Gateway.
        
        Args:
            engine: Core engine components and configuration
        """
        self.engine = engine
        self.model_manager = engine["model_manager"]
        logger.info("API Gateway initialized")
    
    def process_message(self, message: str, session_id: str = "") -> Dict[str, Any]:
        """
        Process a user message for text generation.
        
        Args:
            message: User message
            session_id: Session identifier for conversation context
            
        Returns:
            Dict: Response with generated text
        """
        try:
            from core_engine.src.main import process_text_request
            
            # Generate a session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
                
            logger.info(f"Processing message for session {session_id}")
            response = process_text_request(self.engine, message, session_id)
            
            # Format the response
            return {
                "response": response.get("response", ""),
                "session_id": session_id,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "error": str(e),
                "session_id": session_id,
                "status": "error"
            }
    
    def generate_image(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an image based on the prompt.
        
        Args:
            prompt: Image description
            model: Optional specific model to use
            
        Returns:
            Dict: Response with generated image
        """
        try:
            from core_engine.src.main import process_image_request
            
            logger.info(f"Generating image with prompt: {prompt}")
            response = process_image_request(self.engine, prompt, model)
            
            # Format the response
            return {
                "image": response.get("image", ""),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def generate_video(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a video based on the prompt.
        
        Args:
            prompt: Video description
            model: Optional specific model to use
            
        Returns:
            Dict: Response with generated video
        """
        try:
            from core_engine.src.main import process_video_request
            
            logger.info(f"Generating video with prompt: {prompt}")
            response = process_video_request(self.engine, prompt, model)
            
            # Format the response
            return {
                "video": response.get("video", ""),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def list_models(self) -> Dict[str, Any]:
        """
        Get a list of all available models.
        
        Returns:
            Dict: Dictionary of available models by type
        """
        try:
            from core_engine.src.main import get_available_models
            
            logger.info("Listing available models")
            models = get_available_models(self.engine)
            
            return {
                "models": models,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def clear_conversation(self, session_id: str) -> Dict[str, Any]:
        """
        Clear the conversation history for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Status response
        """
        try:
            from core_engine.src.main import clear_conversation_history
            
            logger.info(f"Clearing conversation history for session {session_id}")
            success = clear_conversation_history(session_id)
            
            if success:
                return {
                    "message": "Conversation history cleared successfully",
                    "session_id": session_id,
                    "status": "success"
                }
            else:
                return {
                    "message": "Session not found",
                    "session_id": session_id,
                    "status": "warning"
                }
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
            return {
                "error": str(e),
                "session_id": session_id,
                "status": "error"
            }
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List available plugins.
        
        Returns:
            List: List of plugin information dictionaries
        """
        # This is a placeholder for plugin functionality
        # In a real implementation, this would query the plugin system
        return [
            {
                "name": "text_generation",
                "description": "Generate text responses",
                "enabled": True
            },
            {
                "name": "image_generation",
                "description": "Generate images from text descriptions",
                "enabled": True
            },
            {
                "name": "video_generation",
                "description": "Generate videos from text descriptions",
                "enabled": True
            }
        ]
