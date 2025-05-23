"""
OpenAI model wrapper implementation.
Provides wrappers for GPT-4 and GPT-3.5-Turbo models.
"""
import os
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
import tiktoken
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.base import BaseModelWrapper

logger = logging.getLogger(__name__)

class OpenAIModelWrapper(BaseModelWrapper):
    """Wrapper for OpenAI language models."""
    
    def __init__(
        self, 
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize the OpenAI model wrapper.
        
        Args:
            model_name: The name of the OpenAI model to use
            api_key: OpenAI API key (defaults to environment variable)
            temperature: Sampling temperature (0.0 to 1.0)
            max_retries: Maximum number of retries on API errors
            timeout: Timeout in seconds for API calls
        """
        self._model_name = model_name
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._temperature = temperature
        self._max_retries = max_retries
        self._timeout = timeout
        
        if not self._api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        
        self._client = openai.AsyncOpenAI(api_key=self._api_key, timeout=timeout)
        self._encoding = tiktoken.encoding_for_model(model_name)
        
        # Model token limits
        self._token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (openai.APIError, openai.APIConnectionError, openai.RateLimitError)
        )
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the OpenAI model.
        
        Args:
            prompt: The input prompt to send to the model
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated text response
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_tokens", 1024),
                top_p=kwargs.get("top_p", 1.0),
                frequency_penalty=kwargs.get("frequency_penalty", 0.0),
                presence_penalty=kwargs.get("presence_penalty", 0.0),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from {self._model_name}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (openai.APIError, openai.APIConnectionError, openai.RateLimitError)
        )
    )
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Generate a streaming response from the OpenAI model.
        
        Args:
            prompt: The input prompt to send to the model
            **kwargs: Additional model-specific parameters
            
        Returns:
            An async iterator of generated text chunks
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_tokens", 1024),
                top_p=kwargs.get("top_p", 1.0),
                frequency_penalty=kwargs.get("frequency_penalty", 0.0),
                presence_penalty=kwargs.get("presence_penalty", 0.0),
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
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
        return len(self._encoding.encode(text))
    
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
        return bool(self._api_key)


class GPT4Wrapper(OpenAIModelWrapper):
    """Specific wrapper for GPT-4 model."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """Initialize the GPT-4 wrapper."""
        super().__init__(
            model_name="gpt-4",
            api_key=api_key,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout
        )


class GPT35TurboWrapper(OpenAIModelWrapper):
    """Specific wrapper for GPT-3.5-Turbo model."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """Initialize the GPT-3.5-Turbo wrapper."""
        super().__init__(
            model_name="gpt-3.5-turbo",
            api_key=api_key,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout
        )
