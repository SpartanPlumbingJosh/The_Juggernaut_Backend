"""
Base memory interface for conversation memory systems.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic

T = TypeVar('T')

class BaseMemory(ABC, Generic[T]):
    """Base class for all memory systems."""
    
    @abstractmethod
    async def add(self, item: T) -> None:
        """
        Add an item to memory.
        
        Args:
            item: The item to add to memory
        """
        pass
    
    @abstractmethod
    async def get(self, key: Any) -> Optional[T]:
        """
        Retrieve an item from memory by key.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The retrieved item, or None if not found
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[T]:
        """
        Search for items in memory.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    async def update(self, key: Any, item: T) -> bool:
        """
        Update an item in memory.
        
        Args:
            key: The key of the item to update
            item: The new item data
            
        Returns:
            True if the update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: Any) -> bool:
        """
        Delete an item from memory.
        
        Args:
            key: The key of the item to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from memory."""
        pass
