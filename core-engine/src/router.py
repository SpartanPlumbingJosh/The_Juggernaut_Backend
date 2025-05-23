"""
Model router implementation for selecting the appropriate language model.
"""
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
import re

from app.models.base import BaseModelWrapper
from app.models.openai_model import GPT4Wrapper, GPT35TurboWrapper
from app.models.opensource_model import LlamaModelWrapper, MistralModelWrapper

logger = logging.getLogger(__name__)

class ModelRouter:
    """
    Router for selecting the appropriate language model based on query complexity.
    Implements fallback mechanisms between models.
    """
    
    def __init__(
        self,
        primary_model: Optional[BaseModelWrapper] = None,
        fallback_models: Optional[List[BaseModelWrapper]] = None,
        complexity_threshold: int = 7,
        token_threshold: int = 2000
    ):
        """
        Initialize the model router.
        
        Args:
            primary_model: The primary model to use (defaults to GPT-4)
            fallback_models: List of fallback models in order of preference
            complexity_threshold: Threshold for determining query complexity (1-10)
            token_threshold: Token count threshold for model selection
        """
        # Initialize default models if not provided
        self._primary_model = primary_model or GPT4Wrapper()
        self._fallback_models = fallback_models or [
            GPT35TurboWrapper(),
            LlamaModelWrapper(),
            MistralModelWrapper()
        ]
        
        # Filter out unavailable models
        self._fallback_models = [model for model in self._fallback_models if model.is_available]
        
        self._complexity_threshold = complexity_threshold
        self._token_threshold = token_threshold
        
        logger.info(f"Model router initialized with primary model: {self._primary_model.model_name}")
        logger.info(f"Fallback models: {[model.model_name for model in self._fallback_models]}")
    
    def _estimate_complexity(self, query: str) -> int:
        """
        Estimate the complexity of a query on a scale of 1-10.
        
        Args:
            query: The query to analyze
            
        Returns:
            Complexity score (1-10)
        """
        # Simple heuristics for complexity estimation
        complexity = 5  # Default medium complexity
        
        # Length-based complexity
        if len(query) > 1000:
            complexity += 2
        elif len(query) < 100:
            complexity -= 1
        
        # Keyword-based complexity
        complex_keywords = [
            "analyze", "compare", "evaluate", "synthesize", "critique",
            "explain", "derive", "prove", "optimize", "debug"
        ]
        for keyword in complex_keywords:
            if re.search(r'\b' + keyword + r'\b', query, re.IGNORECASE):
                complexity += 1
                
        # Cap complexity between 1-10
        return max(1, min(10, complexity))
    
    def _select_model(self, query: str) -> BaseModelWrapper:
        """
        Select the appropriate model based on query complexity and token count.
        
        Args:
            query: The user query
            
        Returns:
            The selected model wrapper
        """
        # Check if primary model is available
        if not self._primary_model.is_available:
            if not self._fallback_models:
                raise RuntimeError("No language models are available")
            return self._fallback_models[0]
        
        # Estimate query complexity
        complexity = self._estimate_complexity(query)
        
        # Estimate token count
        token_count = self._primary_model.get_token_count(query)
        
        logger.debug(f"Query complexity: {complexity}/10, token count: {token_count}")
        
        # Use primary model for complex queries or if within token threshold
        if complexity >= self._complexity_threshold or token_count <= self._token_threshold:
            return self._primary_model
        
        # Use fallback model for simpler queries or if token count is high
        if self._fallback_models:
            return self._fallback_models[0]
        
        # Default to primary model if no fallbacks are available
        return self._primary_model
    
    async def generate(self, query: str, **kwargs) -> str:
        """
        Generate a response using the appropriate model with fallback.
        
        Args:
            query: The user query
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated text response
        """
        # Select initial model
        model = self._select_model(query)
        logger.info(f"Selected model for query: {model.model_name}")
        
        # Try with selected model
        try:
            return await model.generate(query, **kwargs)
        except Exception as e:
            logger.warning(f"Error with {model.model_name}: {str(e)}. Trying fallbacks.")
            
            # Try fallback models in order
            for fallback_model in self._fallback_models:
                if fallback_model.model_name != model.model_name and fallback_model.is_available:
                    try:
                        logger.info(f"Trying fallback model: {fallback_model.model_name}")
                        return await fallback_model.generate(query, **kwargs)
                    except Exception as fallback_error:
                        logger.warning(f"Error with fallback {fallback_model.model_name}: {str(fallback_error)}")
            
            # If all models fail, raise the original error
            raise RuntimeError(f"All models failed to generate a response: {str(e)}")
    
    async def generate_stream(self, query: str, **kwargs) -> AsyncIterator[str]:
        """
        Generate a streaming response using the appropriate model with fallback.
        
        Args:
            query: The user query
            **kwargs: Additional model-specific parameters
            
        Returns:
            An async iterator of generated text chunks
        """
        # Select initial model
        model = self._select_model(query)
        logger.info(f"Selected model for streaming: {model.model_name}")
        
        # Try with selected model
        try:
            async for chunk in model.generate_stream(query, **kwargs):
                yield chunk
        except Exception as e:
            logger.warning(f"Error with {model.model_name} streaming: {str(e)}. Trying fallbacks.")
            
            # Try fallback models in order
            for fallback_model in self._fallback_models:
                if fallback_model.model_name != model.model_name and fallback_model.is_available:
                    try:
                        logger.info(f"Trying fallback model for streaming: {fallback_model.model_name}")
                        # Yield a notification about fallback
                        yield f"\n[Switching to fallback model: {fallback_model.model_name}]\n"
                        
                        async for chunk in fallback_model.generate_stream(query, **kwargs):
                            yield chunk
                        return
                    except Exception as fallback_error:
                        logger.warning(f"Error with fallback {fallback_model.model_name} streaming: {str(fallback_error)}")
            
            # If all models fail, yield an error message
            yield "\n[Error: All models failed to generate a streaming response. Please try again later.]\n"
