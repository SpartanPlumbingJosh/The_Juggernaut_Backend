"""
Ollama API Client

This module provides a client for interacting with the Ollama API.
It handles the low-level API calls and error handling.
"""

import requests
import logging
import json
import base64
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaAPIClient:
    """
    Client for interacting with the Ollama API.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama API Client.
        
        Args:
            base_url: Base URL for the Ollama API
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available models.
        
        Returns:
            List: List of model information dictionaries
        """
        try:
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Failed to list models: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
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
    
    def generate(self, model: str, prompt: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Generate content using the specified model.
        
        Args:
            model: Name of the model to use
            prompt: Prompt for generation
            stream: Whether to stream the response
            **kwargs: Additional parameters for the generation
            
        Returns:
            Dict: Response from the model
        """
        try:
            # Set default parameters
            params = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/generate", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating content: {response.text}")
                return {"error": f"Failed to generate content: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in generate: {str(e)}")
            return {"error": str(e)}
    
    def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Chat with the specified model.
        
        Args:
            model: Name of the model to use
            messages: List of message dictionaries (role, content)
            stream: Whether to stream the response
            **kwargs: Additional parameters for the chat
            
        Returns:
            Dict: Response from the model
        """
        try:
            # Set default parameters
            params = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make API request
            response = requests.post(f"{self.api_url}/chat", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error in chat: {response.text}")
                return {"error": f"Failed in chat: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in chat: {str(e)}")
            return {"error": str(e)}
    
    def embeddings(self, model: str, prompt: str) -> Dict[str, Any]:
        """
        Get embeddings for the specified prompt.
        
        Args:
            model: Name of the model to use
            prompt: Text to get embeddings for
            
        Returns:
            Dict: Response containing embeddings
        """
        try:
            params = {
                "model": model,
                "prompt": prompt
            }
            
            response = requests.post(f"{self.api_url}/embeddings", json=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting embeddings: {response.text}")
                return {"error": f"Failed to get embeddings: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in embeddings: {str(e)}")
            return {"error": str(e)}
