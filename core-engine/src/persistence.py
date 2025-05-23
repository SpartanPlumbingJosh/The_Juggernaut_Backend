"""
Memory persistence layer for storing and retrieving memory data.
"""
import logging
import os
import json
import aiosqlite
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

from app.memory.conversation import Conversation, Message
from app.memory.vector_db import VectorDBClient

logger = logging.getLogger(__name__)

class MemoryPersistence:
    """
    Memory persistence layer for storing and retrieving memory data.
    Handles both conversation memory and vector database persistence.
    """
    
    def __init__(
        self,
        db_path: str = "/home/ubuntu/core-engine/data/memory.db",
        vector_db_client: Optional[VectorDBClient] = None
    ):
        """
        Initialize the memory persistence layer.
        
        Args:
            db_path: Path to the SQLite database file
            vector_db_client: Vector database client for semantic search
        """
        self._db_path = db_path
        self._vector_db_client = vector_db_client
        self._initialized = False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async def initialize(self) -> bool:
        """
        Initialize the memory persistence layer.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize SQLite database
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                ''')
                
                await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
                ''')
                
                await db.execute('''
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                ''')
                
                await db.commit()
            
            # Initialize vector database if provided
            if self._vector_db_client:
                await self._vector_db_client.initialize()
                
                # Create default collections
                await self._vector_db_client.create_collection("knowledge")
                await self._vector_db_client.create_collection("episodic_memory")
            
            self._initialized = True
            logger.info("Memory persistence layer initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory persistence layer: {str(e)}")
            return False
    
    async def save_conversation(self, conversation: Conversation) -> bool:
        """
        Save a conversation to the database.
        
        Args:
            conversation: The conversation to save
            
        Returns:
            True if the save was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Save conversation
                await db.execute(
                    '''
                    INSERT OR REPLACE INTO conversations 
                    (conversation_id, title, metadata, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        conversation.conversation_id,
                        conversation.title,
                        json.dumps(conversation.metadata),
                        conversation.created_at.isoformat(),
                        conversation.updated_at.isoformat()
                    )
                )
                
                # Save messages
                for message in conversation.messages:
                    await db.execute(
                        '''
                        INSERT OR REPLACE INTO messages 
                        (message_id, conversation_id, role, content, timestamp, metadata) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            message.message_id,
                            conversation.conversation_id,
                            message.role,
                            message.content,
                            message.timestamp.isoformat(),
                            json.dumps(message.metadata)
                        )
                    )
                
                await db.commit()
            
            logger.info(f"Saved conversation {conversation.conversation_id} with {len(conversation.messages)} messages")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.conversation_id}: {str(e)}")
            return False
    
    async def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from the database.
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            The loaded conversation, or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Load conversation
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    'SELECT * FROM conversations WHERE conversation_id = ?',
                    (conversation_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                conversation = Conversation(
                    conversation_id=row['conversation_id'],
                    title=row['title'],
                    metadata=json.loads(row['metadata']),
                )
                conversation.created_at = datetime.fromisoformat(row['created_at'])
                conversation.updated_at = datetime.fromisoformat(row['updated_at'])
                
                # Load messages
                cursor = await db.execute(
                    'SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp',
                    (conversation_id,)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    message = Message(
                        role=row['role'],
                        content=row['content'],
                        message_id=row['message_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        metadata=json.loads(row['metadata'])
                    )
                    conversation.messages.append(message)
                
                logger.info(f"Loaded conversation {conversation_id} with {len(conversation.messages)} messages")
                return conversation
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {str(e)}")
            return None
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from the database.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Delete messages first (foreign key constraint)
                await db.execute(
                    'DELETE FROM messages WHERE conversation_id = ?',
                    (conversation_id,)
                )
                
                # Delete conversation
                await db.execute(
                    'DELETE FROM conversations WHERE conversation_id = ?',
                    (conversation_id,)
                )
                
                await db.commit()
            
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False
    
    async def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversations from the database.
        
        Args:
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of conversation summaries
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    '''
                    SELECT c.*, COUNT(m.message_id) as message_count 
                    FROM conversations c 
                    LEFT JOIN messages m ON c.conversation_id = m.conversation_id 
                    GROUP BY c.conversation_id 
                    ORDER BY c.updated_at DESC 
                    LIMIT ? OFFSET ?
                    ''',
                    (limit, offset)
                )
                rows = await cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append({
                        "conversation_id": row['conversation_id'],
                        "title": row['title'],
                        "metadata": json.loads(row['metadata']),
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at'],
                        "message_count": row['message_count']
                    })
                
                return conversations
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return []
    
    async def add_to_knowledge_base(
        self, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the knowledge base.
        
        Args:
            texts: List of text documents to add
            metadata: List of metadata dictionaries for each document
            ids: Optional list of IDs for the documents
            
        Returns:
            List of document IDs
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._vector_db_client:
            logger.error("No vector database client provided")
            return []
        
        try:
            return await self._vector_db_client.insert(
                collection_name="knowledge",
                texts=texts,
                metadata=metadata,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {str(e)}")
            return []
    
    async def search_knowledge_base(
        self, 
        query: str, 
        limit: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._vector_db_client:
            logger.error("No vector database client provided")
            return []
        
        try:
            return await self._vector_db_client.search(
                collection_name="knowledge",
                query=query,
                limit=limit,
                filter=filter
            )
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    async def add_episodic_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add an episodic memory.
        
        Args:
            user_id: ID of the user
            memory_type: Type of memory (e.g., "preference", "fact", "interaction")
            content: Memory content
            metadata: Additional metadata
            
        Returns:
            ID of the added memory, or None if failed
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            metadata = metadata or {}
            
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    '''
                    INSERT INTO episodic_memory 
                    (memory_id, user_id, memory_type, content, timestamp, metadata) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        memory_id,
                        user_id,
                        memory_type,
                        content,
                        timestamp,
                        json.dumps(metadata)
                    )
                )
                
                await db.commit()
            
            # Add to vector database if available
            if self._vector_db_client:
                await self._vector_db_client.insert(
                    collection_name="episodic_memory",
                    texts=[content],
                    metadata=[{
                        "memory_id": memory_id,
                        "user_id": user_id,
                        "memory_type": memory_type,
                        "timestamp": timestamp,
                        **metadata
                    }],
                    ids=[memory_id]
                )
            
            logger.info(f"Added episodic memory {memory_id} for user {user_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error adding episodic memory for user {user_id}: {str(e)}")
            return None
    
    async def search_episodic_memory(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search episodic memories.
        
        Args:
            user_id: ID of the user
            query: Search query
            memory_type: Optional type of memory to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of matching memories
        """
        if not self._initialized:
            await self.initialize()
        
        # Use vector search if available
        if self._vector_db_client:
            try:
                filter = {"user_id": user_id}
                if memory_type:
                    filter["memory_type"] = memory_type
                
                return await self._vector_db_client.search(
                    collection_name="episodic_memory",
                    query=query,
                    limit=limit,
                    filter=filter
                )
            except Exception as e:
                logger.error(f"Error searching episodic memory with vector DB: {str(e)}")
        
        # Fall back to SQL search
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Basic SQL search (not as effective as vector search)
                sql = '''
                SELECT * FROM episodic_memory 
                WHERE user_id = ? AND content LIKE ? 
                '''
                params = [user_id, f"%{query}%"]
                
                if memory_type:
                    sql += "AND memory_type = ? "
                    params.append(memory_type)
                
                sql += "ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(sql, params)
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row['memory_id'],
                        "text": row['content'],
                        "metadata": {
                            "user_id": row['user_id'],
                            "memory_type": row['memory_type'],
                            "timestamp": row['timestamp'],
                            **json.loads(row['metadata'])
                        },
                        "score": 1.0  # Placeholder score for SQL search
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error searching episodic memory with SQL: {str(e)}")
            return []
