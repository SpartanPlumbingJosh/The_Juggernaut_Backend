"""
Open-source model wrapper implementation.
Provides wrappers for Llama 2 and Mistral models.
"""
import os
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
import tiktoken
from langchain_community.llms import HuggingFacePipeline
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from app.models.base import BaseModelWrapper

logger = logging.getLogger(__name__)

class OpenSourceModelWrapper(BaseModelWrapper):
    """Wrapper for open-source language models."""
    
    def __init__(
        self, 
        model_name: str = "meta-llama/Llama-2-7b-chat-hf",
        temperature: float = 0.7,
        max_length: int = 1024,
        device: str = "cpu"
    ):
        """
        Initialize the open-source model wrapper.
        
        Args:
            model_name: The name of the model to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_length: Maximum length of generated text
            device: Device to run the model on ("cpu" or "cuda")
        """
        self._model_name = model_name
        self._temperature = temperature
        self._max_length = max_length
        self._device = device
        
        # Model token limits (approximate)
        self._token_limits = {
            "meta-llama/Llama-2-7b-chat-hf": 4096,
            "meta-llama/Llama-2-13b-chat-hf": 4096,
            "mistralai/Mistral-7B-Instruct-v0.1": 8192
        }
        
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map=device,
                torch_dtype="auto"
            )
            self._pipe = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                max_length=max_length,
                temperature=temperature,
                top_p=0.95,
                repetition_penalty=1.1
            )
            self._llm = HuggingFacePipeline(pipeline=self._pipe)
            self._is_available = True
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            self._is_available = False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the open-source model.
        
        Args:
            prompt: The input prompt to send to the model
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated text response
        """
        if not self._is_available:
            raise RuntimeError(f"Model {self._model_name} is not available")
        
        try:
            response = self._llm(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating response from {self._model_name}: {str(e)}")
            raise
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Generate a streaming response from the open-source model.
        
        Args:
            prompt: The input prompt to send to the model
            **kwargs: Additional model-specific parameters
            
        Returns:
            An async iterator of generated text chunks
        """
        if not self._is_available:
            raise RuntimeError(f"Model {self._model_name} is not available")
        
        try:
            # Create a custom callback handler to capture streaming output
            class AsyncIteratorCallbackHandler(StreamingStdOutCallbackHandler):
                def __init__(self):
                    super().__init__()
                    self.tokens = []
                
                def on_llm_new_token(self, token: str, **kwargs) -> None:
                    self.tokens.append(token)
            
            callback = AsyncIteratorCallbackHandler()
            
            # Run the model with the callback
            self._llm(prompt, callbacks=[callback])
            
            # Yield each token
            for token in callback.tokens:
                yield token
        except Exception as e:
            logger.error(f"Error generating streaming response from {self._model_name}: {str(e)}")
            raise
    
    def get_token_count(self, text: str) -> int:
        """
        Count the number of tokens in the given text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens
        """
        if not self._is_available:
            return 0
        
        return len(self._tokenizer.encode(text))
    
    @property
    def max_tokens(self) -> int:
        """
        Get the maximum number of tokens the model can handle.
        
        Returns:
            The maximum token limit
        """
        return self._token_limits.get(self._model_name, 4096)
    
    @property
    def model_name(self) -> str:
        """
        Get the name of the model.
        
        Returns:
            The model name
        """
        return self._model_name
    
    @property
    def is_available(self) -> bool:
        """
        Check if the model is currently available.
        
        Returns:
            True if the model is available, False otherwise
        """
        return self._is_available


class LlamaModelWrapper(OpenSourceModelWrapper):
    """Specific wrapper for Llama 2 model."""
    
    def __init__(
        self,
        temperature: float = 0.7,
        max_length: int = 1024,
        device: str = "cpu"
    ):
        """Initialize the Llama 2 wrapper."""
        super().__init__(
            model_name="meta-llama/Llama-2-7b-chat-hf",
            temperature=temperature,
            max_length=max_length,
            device=device
        )


class MistralModelWrapper(OpenSourceModelWrapper):
    """Specific wrapper for Mistral model."""
    
    def __init__(
        self,
        temperature: float = 0.7,
        max_length: int = 1024,
        device: str = "cpu"
    ):
        """Initialize the Mistral wrapper."""
        super().__init__(
            model_name="mistralai/Mistral-7B-Instruct-v0.1",
            temperature=temperature,
            max_length=max_length,
            device=device
        )
