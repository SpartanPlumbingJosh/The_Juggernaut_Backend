"""
Model Manager for Ollama Integration

This module handles the management of multiple Ollama models for text, image, and video generation.
It provides a unified interface for model selection, routing, and fallback mechanisms.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaModelManager:
    """
    Manages multiple Ollama models for text, image, and video generation.
    Provides routing, fallback, and resource management capabilities.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama Model Manager.
        
        Args:
            base_url: Base URL for the Ollama API
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
        # Define model configurations
        self.text_models = {
            "primary": "mistral:7b-instruct-v0.3",
            "secondary": "mixtral:8x7b-instruct-v0.1",
            "code": "codellama:7b-instruct",
            "fallback": "mistral:7b-instruct-v0.3"  # Fallback is same as primary for now
        }
        
        self.image_models = {
            "primary": "stable-diffusion-xl",
            "artistic": "playground-v2",
            "fallback": "stable-diffusion"
        }
        
        self.video_models = {
            "primary": "stable-video-diffusion",
            "animation": "animatediff",
            "fallback": "stable-video-diffusion"
        }
        
        # Check available models and pull if needed
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """
        Check which models are available and pull missing ones.
        """
        try:
            # Get list of available models
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json()["models"]]
                logger.info(f"Available models: {available_models}")
                
                # Check and pull text models
                for model_type, model_name in self.text_models.items():
                    if model_name not in available_models:
                        logger.info(f"Pulling text model: {model_name}")
                        self._pull_model(model_name)
                
                # Check and pull image models
                for model_type, model_name in self.image_models.items():
                    if model_name not in available_models:
                        logger.info(f"Pulling image model: {model_name}")
                        self._pull_model(model_name)
                
                # Check and pull video models
                for model_type, model_name in self.video_models.items():
                    if model_name not in available_models:
                        logger.info(f"Pulling video model: {model_name}")
                        self._pull_model(model_name)
            else:
                logger.error(f"Failed to get available models: {response.text}")
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
    
    def _pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/pull",
                json={"name": model_name}
            )
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model_name}")
                return True
            else:
                logger.error(f"Failed to pull model {model_name}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {str(e)}")
            return False
    
    def select_text_model(self, query: str) -> str:
        """
        Select the appropriate text model based on the query content.
        
        Args:
            query: User query text
            
        Returns:
            str: Selected model name
        """
        # Check if query is code-related
        code_keywords = ["code", "function", "programming", "python", "javascript", "java", "c++", "html", "css"]
        if any(keyword in query.lower() for keyword in code_keywords):
            return self.text_models["code"]
        
        # Check if query is complex (long or has complex reasoning indicators)
        complex_indicators = ["explain", "analyze", "compare", "contrast", "evaluate", "synthesize"]
        if len(query.split()) > 50 or any(indicator in query.lower() for indicator in complex_indicators):
            return self.text_models["secondary"]
        
        # Default to primary model
        return self.text_models["primary"]
    
    def generate_text(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate text using the selected Ollama model.
        
        Args:
            prompt: Text prompt
            model: Specific model to use (if None, will auto-select)
            **kwargs: Additional parameters for the generation
            
        Returns:
            Dict: Response from the model
        """
        try:
            # Select model if not specified
            if model is None:
                model = self.select_text_model(prompt)
            
            # Set default parameters
            params = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/generate", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating text: {response.text}")
                
                # Try fallback model if different from the current one
                if model != self.text_models["fallback"]:
                    logger.info(f"Trying fallback model: {self.text_models['fallback']}")
                    return self.generate_text(prompt, self.text_models["fallback"], **kwargs)
                
                return {"error": f"Failed to generate text: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in generate_text: {str(e)}")
            return {"error": str(e)}
    
    def chat_with_history(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Chat with the model using conversation history.
        
        Args:
            messages: List of message dictionaries (role, content)
            model: Specific model to use (if None, will use primary)
            **kwargs: Additional parameters
            
        Returns:
            Dict: Response from the model
        """
        try:
            # Select model if not specified
            if model is None:
                model = self.text_models["primary"]
            
            # Make API request using the chat endpoint
            params = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/chat", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error in chat: {response.text}")
                
                # Try fallback model if different from the current one
                if model != self.text_models["fallback"]:
                    logger.info(f"Trying fallback model: {self.text_models['fallback']}")
                    return self.chat_with_history(messages, self.text_models["fallback"], **kwargs)
                
                return {"error": f"Failed in chat: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in chat: {str(e)}")
            return {"error": str(e)}
    
    def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate an image using the selected Ollama model.
        
        Args:
            prompt: Image description
            model: Specific model to use (if None, will use primary)
            **kwargs: Additional parameters for the generation
            
        Returns:
            Dict: Response containing the generated image
        """
        try:
            # Select model if not specified
            if model is None:
                model = self.image_models["primary"]
            
            # Set default parameters
            params = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/generate", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating image: {response.text}")
                
                # Try fallback model if different from the current one
                if model != self.image_models["fallback"]:
                    logger.info(f"Trying fallback model: {self.image_models['fallback']}")
                    return self.generate_image(prompt, self.image_models["fallback"], **kwargs)
                
                return {"error": f"Failed to generate image: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in generate_image: {str(e)}")
            return {"error": str(e)}
    
    def generate_video(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a video using the selected Ollama model.
        
        Args:
            prompt: Video description
            model: Specific model to use (if None, will use primary)
            **kwargs: Additional parameters for the generation
            
        Returns:
            Dict: Response containing the generated video
        """
        try:
            # Select model if not specified
            if model is None:
                model = self.video_models["primary"]
            
            # Set default parameters
            params = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/generate", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating video: {response.text}")
                
                # Try fallback model if different from the current one
                if model != self.video_models["fallback"]:
                    logger.info(f"Trying fallback model: {self.video_models['fallback']}")
                    return self.generate_video(prompt, self.video_models["fallback"], **kwargs)
                
                return {"error": f"Failed to generate video: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in generate_video: {str(e)}")
            return {"error": str(e)}
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get a list of all available models.
        
        Returns:
            Dict: Dictionary of available models by type
        """
        try:
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json()["models"]]
                
                return {
                    "text": [model for model in available_models if model in self.text_models.values()],
                    "image": [model for model in available_models if model in self.image_models.values()],
                    "video": [model for model in available_models if model in self.video_models.values()]
                }
            else:
                logger.error(f"Failed to get available models: {response.text}")
                return {"text": [], "image": [], "video": []}
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return {"text": [], "image": [], "video": []}
