"""
Context retrieval mechanisms for the Core Conversational Engine.
"""
import logging
from typing import Dict, List, Optional, Any, Union
import json

from app.memory.persistence import MemoryPersistence
from app.memory.conversation import Conversation, Message

logger = logging.getLogger(__name__)

class ContextRetrieval:
    """
    Context retrieval system for retrieving relevant context for conversations.
    Combines conversation history, knowledge base, and episodic memory.
    """
    
    def __init__(
        self,
        memory_persistence: MemoryPersistence,
        max_conversation_messages: int = 10,
        max_knowledge_results: int = 3,
        max_episodic_results: int = 3
    ):
        """
        Initialize the context retrieval system.
        
        Args:
            memory_persistence: Memory persistence layer
            max_conversation_messages: Maximum number of conversation messages to include
            max_knowledge_results: Maximum number of knowledge base results to include
            max_episodic_results: Maximum number of episodic memory results to include
        """
        self._memory_persistence = memory_persistence
        self._max_conversation_messages = max_conversation_messages
        self._max_knowledge_results = max_knowledge_results
        self._max_episodic_results = max_episodic_results
    
    async def get_conversation_context(self, conversation_id: str) -> str:
        """
        Get formatted conversation history context.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Formatted conversation history
        """
        conversation = await self._memory_persistence.load_conversation(conversation_id)
        if not conversation:
            return ""
        
        # Get recent messages
        recent_messages = conversation.get_messages(self._max_conversation_messages)
        
        # Format messages
        formatted = []
        for message in recent_messages:
            formatted.append(f"{message.role.capitalize()}: {message.content}")
        
        return "\n\n".join(formatted)
    
    async def get_knowledge_context(self, query: str) -> str:
        """
        Get relevant knowledge context for a query.
        
        Args:
            query: The query to search for
            
        Returns:
            Formatted knowledge context
        """
        results = await self._memory_persistence.search_knowledge_base(
            query=query,
            limit=self._max_knowledge_results
        )
        
        if not results:
            return ""
        
        # Format results
        formatted = ["Relevant Knowledge:"]
        for i, result in enumerate(results):
            formatted.append(f"{i+1}. {result['text']}")
        
        return "\n\n".join(formatted)
    
    async def get_episodic_context(self, user_id: str, query: str) -> str:
        """
        Get relevant episodic memory context for a query.
        
        Args:
            user_id: ID of the user
            query: The query to search for
            
        Returns:
            Formatted episodic memory context
        """
        results = await self._memory_persistence.search_episodic_memory(
            user_id=user_id,
            query=query,
            limit=self._max_episodic_results
        )
        
        if not results:
            return ""
        
        # Format results
        formatted = ["User Information:"]
        for i, result in enumerate(results):
            memory_type = result['metadata'].get('memory_type', 'information')
            formatted.append(f"{memory_type.capitalize()}: {result['text']}")
        
        return "\n\n".join(formatted)
    
    async def get_combined_context(
        self,
        conversation_id: str,
        user_id: str,
        query: str
    ) -> Dict[str, str]:
        """
        Get combined context from all sources.
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user
            query: The current query
            
        Returns:
            Dictionary with different context types
        """
        # Get contexts in parallel (in a real implementation)
        conversation_context = await self.get_conversation_context(conversation_id)
        knowledge_context = await self.get_knowledge_context(query)
        episodic_context = await self.get_episodic_context(user_id, query)
        
        return {
            "conversation_history": conversation_context,
            "knowledge_context": knowledge_context,
            "user_context": episodic_context
        }
    
    async def extract_learning(self, conversation: Conversation, user_id: str) -> List[Dict[str, Any]]:
        """
        Extract learning from a conversation for episodic memory.
        
        Args:
            conversation: The conversation to analyze
            user_id: ID of the user
            
        Returns:
            List of extracted learnings
        """
        # This is a simplified implementation
        # In a real system, this would use an LLM to extract learnings
        
        learnings = []
        preference_keywords = ["prefer", "like", "favorite", "hate", "dislike"]
        fact_keywords = ["my name is", "I am", "I'm", "I live", "my job", "my email"]
        
        for message in conversation.messages:
            if message.role != "user":
                continue
            
            content = message.content.lower()
            
            # Check for preferences
            for keyword in preference_keywords:
                if keyword in content:
                    learnings.append({
                        "user_id": user_id,
                        "memory_type": "preference",
                        "content": message.content,
                        "metadata": {
                            "source": "conversation",
                            "conversation_id": conversation.conversation_id,
                            "message_id": message.message_id,
                            "keyword": keyword
                        }
                    })
                    break
            
            # Check for facts
            for keyword in fact_keywords:
                if keyword in content:
                    learnings.append({
                        "user_id": user_id,
                        "memory_type": "fact",
                        "content": message.content,
                        "metadata": {
                            "source": "conversation",
                            "conversation_id": conversation.conversation_id,
                            "message_id": message.message_id,
                            "keyword": keyword
                        }
                    })
                    break
        
        return learnings
    
    async def save_learnings(self, learnings: List[Dict[str, Any]]) -> List[str]:
        """
        Save extracted learnings to episodic memory.
        
        Args:
            learnings: List of extracted learnings
            
        Returns:
            List of saved memory IDs
        """
        memory_ids = []
        
        for learning in learnings:
            memory_id = await self._memory_persistence.add_episodic_memory(
                user_id=learning["user_id"],
                memory_type=learning["memory_type"],
                content=learning["content"],
                metadata=learning["metadata"]
            )
            
            if memory_id:
                memory_ids.append(memory_id)
        
        return memory_ids
