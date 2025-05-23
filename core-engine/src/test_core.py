"""
Test script for Core Conversational Engine.
"""
import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from app.api.auth import create_access_token
from app.memory.conversation import Conversation, Message
from app.memory.persistence import MemoryPersistence
from app.memory.vector_db import VectorDBFactory, ChromaDBClient
from app.memory.retrieval import ContextRetrieval
from app.models.router import ModelRouter
from app.models.openai_model import GPT4Wrapper, GPT35TurboWrapper


async def test_memory_persistence():
    """Test memory persistence functionality."""
    logger.info("Testing memory persistence...")
    
    # Initialize persistence
    persistence = MemoryPersistence()
    await persistence.initialize()
    
    # Create test conversation
    conversation = Conversation(
        title="Test Conversation",
        metadata={"user_id": "test_user"}
    )
    
    # Add messages
    conversation.add_message(Message(
        role="user",
        content="Hello, how are you?",
        metadata={"source": "test"}
    ))
    
    conversation.add_message(Message(
        role="assistant",
        content="I'm doing well, thank you for asking!",
        metadata={"source": "test", "model": "gpt-4"}
    ))
    
    # Save conversation
    success = await persistence.save_conversation(conversation)
    assert success, "Failed to save conversation"
    logger.info(f"Saved conversation: {conversation.conversation_id}")
    
    # Load conversation
    loaded_conversation = await persistence.load_conversation(conversation.conversation_id)
    assert loaded_conversation is not None, "Failed to load conversation"
    assert loaded_conversation.title == conversation.title, "Conversation title mismatch"
    assert len(loaded_conversation.messages) == 2, "Message count mismatch"
    logger.info(f"Loaded conversation: {loaded_conversation.conversation_id}")
    
    # Add episodic memory
    memory_id = await persistence.add_episodic_memory(
        user_id="test_user",
        memory_type="preference",
        content="I prefer dark mode interfaces",
        metadata={"source": "test"}
    )
    assert memory_id is not None, "Failed to add episodic memory"
    logger.info(f"Added episodic memory: {memory_id}")
    
    # Search episodic memory
    results = await persistence.search_episodic_memory(
        user_id="test_user",
        query="dark mode"
    )
    assert len(results) > 0, "No episodic memory results found"
    logger.info(f"Found {len(results)} episodic memory results")
    
    # Delete conversation
    success = await persistence.delete_conversation(conversation.conversation_id)
    assert success, "Failed to delete conversation"
    logger.info(f"Deleted conversation: {conversation.conversation_id}")
    
    logger.info("Memory persistence tests passed!")


async def test_vector_db():
    """Test vector database functionality."""
    logger.info("Testing vector database...")
    
    # Create ChromaDB client
    client = ChromaDBClient()
    await client.initialize()
    
    # Create test collection
    collection_name = f"test_collection_{int(time.time())}"
    success = await client.create_collection(collection_name)
    assert success, "Failed to create collection"
    logger.info(f"Created collection: {collection_name}")
    
    # List collections
    collections = await client.list_collections()
    assert collection_name in collections, "Collection not found in list"
    logger.info(f"Found collections: {collections}")
    
    # Insert documents
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language for data science"
    ]
    metadata = [
        {"source": "test", "category": "example"},
        {"source": "test", "category": "ai"},
        {"source": "test", "category": "programming"}
    ]
    ids = await client.insert(collection_name, texts, metadata)
    assert len(ids) == 3, "Failed to insert all documents"
    logger.info(f"Inserted documents with IDs: {ids}")
    
    # Search documents
    results = await client.search(collection_name, "artificial intelligence")
    assert len(results) > 0, "No search results found"
    logger.info(f"Found {len(results)} search results")
    
    # Delete collection
    success = await client.delete_collection(collection_name)
    assert success, "Failed to delete collection"
    logger.info(f"Deleted collection: {collection_name}")
    
    logger.info("Vector database tests passed!")


async def test_model_router():
    """Test model router functionality."""
    logger.info("Testing model router...")
    
    # Create model router
    router = ModelRouter(
        primary_model=GPT35TurboWrapper(),  # Using GPT-3.5 for testing to save costs
        fallback_models=[]
    )
    
    # Test query complexity estimation
    simple_query = "What's the weather like today?"
    complex_query = "Can you analyze the implications of quantum computing on modern cryptography and explain how Shor's algorithm threatens RSA encryption?"
    
    simple_complexity = router._estimate_complexity(simple_query)
    complex_complexity = router._estimate_complexity(complex_query)
    
    assert simple_complexity < complex_complexity, "Complexity estimation failed"
    logger.info(f"Simple query complexity: {simple_complexity}")
    logger.info(f"Complex query complexity: {complex_complexity}")
    
    # Test model selection
    selected_model = router._select_model(simple_query)
    assert selected_model is not None, "Model selection failed"
    logger.info(f"Selected model: {selected_model.model_name}")
    
    # Test generation (commented out to avoid API costs during testing)
    # response = await router.generate("Hello, how are you?")
    # assert response, "Generation failed"
    # logger.info(f"Generated response: {response[:50]}...")
    
    logger.info("Model router tests passed!")


async def test_auth():
    """Test authentication functionality."""
    logger.info("Testing authentication...")
    
    # Create test token
    token_data = {
        "sub": "test_user",
        "scopes": ["conversation:read", "conversation:write", "memory:read"]
    }
    token = create_access_token(token_data)
    assert token, "Failed to create token"
    logger.info(f"Created token: {token[:20]}...")
    
    logger.info("Authentication tests passed!")


async def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")
    
    try:
        await test_memory_persistence()
        await test_vector_db()
        await test_model_router()
        await test_auth()
        
        logger.info("All tests passed!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_tests())
