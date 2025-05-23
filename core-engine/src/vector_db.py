"""
Vector database abstraction layer for long-term memory storage.
Supports both Pinecone and ChromaDB.
"""
import logging
import os
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
import uuid
import json

import pinecone
from pinecone import Pinecone, ServerlessSpec
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorDBClient(ABC):
    """Abstract base class for vector database clients."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the vector database client.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str) -> bool:
        """
        Create a new collection in the vector database.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from the vector database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_collections(self) -> List[str]:
        """
        List all collections in the vector database.
        
        Returns:
            List of collection names
        """
        pass
    
    @abstractmethod
    async def insert(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Insert documents into a collection.
        
        Args:
            collection_name: Name of the collection
            texts: List of text documents to insert
            metadata: List of metadata dictionaries for each document
            ids: Optional list of IDs for the documents (generated if not provided)
            
        Returns:
            List of inserted document IDs
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        collection_name: str, 
        query: str, 
        limit: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Search query
            limit: Maximum number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results with document ID, text, metadata, and score
        """
        pass
    
    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete documents from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get(self, collection_name: str, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get documents by ID from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to retrieve
            
        Returns:
            List of documents with ID, text, and metadata
        """
        pass


class PineconeClient(VectorDBClient):
    """Pinecone vector database client implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        dimension: int = 1536,  # Default for OpenAI embeddings
        metric: str = "cosine"
    ):
        """
        Initialize the Pinecone client.
        
        Args:
            api_key: Pinecone API key (defaults to environment variable)
            environment: Pinecone environment (defaults to environment variable)
            dimension: Dimension of the embedding vectors
            metric: Distance metric to use (cosine, euclidean, dotproduct)
        """
        self._api_key = api_key or os.getenv("PINECONE_API_KEY")
        self._environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        self._dimension = dimension
        self._metric = metric
        self._initialized = False
        
        if not self._api_key or not self._environment:
            logger.warning("Pinecone API key or environment not provided.")
    
    async def initialize(self) -> bool:
        """
        Initialize the Pinecone client.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self._client = Pinecone(api_key=self._api_key)
            self._initialized = True
            logger.info("Pinecone client initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Error initializing Pinecone client: {str(e)}")
            return False
    
    async def create_collection(self, collection_name: str) -> bool:
        """
        Create a new index in Pinecone.
        
        Args:
            collection_name: Name of the index to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if index exists
            indexes = self._client.list_indexes()
            index_names = [index.name for index in indexes]
            
            if collection_name not in index_names:
                self._client.create_index(
                    name=collection_name,
                    dimension=self._dimension,
                    metric=self._metric,
                    spec=ServerlessSpec(cloud="aws", region="us-west-2")
                )
                logger.info(f"Created Pinecone index: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating Pinecone index {collection_name}: {str(e)}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete an index from Pinecone.
        
        Args:
            collection_name: Name of the index to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if index exists
            indexes = self._client.list_indexes()
            index_names = [index.name for index in indexes]
            
            if collection_name in index_names:
                self._client.delete_index(collection_name)
                logger.info(f"Deleted Pinecone index: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting Pinecone index {collection_name}: {str(e)}")
            return False
    
    async def list_collections(self) -> List[str]:
        """
        List all indexes in Pinecone.
        
        Returns:
            List of index names
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            indexes = self._client.list_indexes()
            return [index.name for index in indexes]
        except Exception as e:
            logger.error(f"Error listing Pinecone indexes: {str(e)}")
            return []
    
    async def insert(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Insert documents into a Pinecone index.
        
        Args:
            collection_name: Name of the index
            texts: List of text documents to insert
            metadata: List of metadata dictionaries for each document
            ids: Optional list of IDs for the documents (generated if not provided)
            
        Returns:
            List of inserted document IDs
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # Get embeddings for texts (placeholder - in real implementation, use embedding model)
            # This is a simplified version - in production, use actual embeddings
            embeddings = [[0.0] * self._dimension for _ in range(len(texts))]
            
            # Get index
            index = self._client.Index(collection_name)
            
            # Prepare vectors
            vectors = []
            for i in range(len(texts)):
                vectors.append({
                    "id": ids[i],
                    "values": embeddings[i],
                    "metadata": {
                        "text": texts[i],
                        **metadata[i]
                    }
                })
            
            # Upsert vectors
            index.upsert(vectors=vectors)
            
            logger.info(f"Inserted {len(texts)} documents into Pinecone index {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Error inserting into Pinecone index {collection_name}: {str(e)}")
            return []
    
    async def search(
        self, 
        collection_name: str, 
        query: str, 
        limit: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents in a Pinecone index.
        
        Args:
            collection_name: Name of the index
            query: Search query
            limit: Maximum number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results with document ID, text, metadata, and score
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get embedding for query (placeholder - in real implementation, use embedding model)
            # This is a simplified version - in production, use actual embeddings
            query_embedding = [0.0] * self._dimension
            
            # Get index
            index = self._client.Index(collection_name)
            
            # Query index
            results = index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter=filter
            )
            
            # Format results
            formatted_results = []
            for match in results["matches"]:
                formatted_results.append({
                    "id": match["id"],
                    "text": match["metadata"].get("text", ""),
                    "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
                    "score": match["score"]
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching Pinecone index {collection_name}: {str(e)}")
            return []
    
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete documents from a Pinecone index.
        
        Args:
            collection_name: Name of the index
            ids: List of document IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get index
            index = self._client.Index(collection_name)
            
            # Delete vectors
            index.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from Pinecone index {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from Pinecone index {collection_name}: {str(e)}")
            return False
    
    async def get(self, collection_name: str, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get documents by ID from a Pinecone index.
        
        Args:
            collection_name: Name of the index
            ids: List of document IDs to retrieve
            
        Returns:
            List of documents with ID, text, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get index
            index = self._client.Index(collection_name)
            
            # Fetch vectors
            results = index.fetch(ids=ids)
            
            # Format results
            formatted_results = []
            for id, vector in results["vectors"].items():
                formatted_results.append({
                    "id": id,
                    "text": vector["metadata"].get("text", ""),
                    "metadata": {k: v for k, v in vector["metadata"].items() if k != "text"}
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error fetching from Pinecone index {collection_name}: {str(e)}")
            return []


class ChromaDBClient(VectorDBClient):
    """ChromaDB vector database client implementation."""
    
    def __init__(
        self,
        persist_directory: str = "/home/ubuntu/core-engine/data/chromadb",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialize the ChromaDB client.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedding_function: Embedding function to use (defaults to OpenAI)
        """
        self._persist_directory = persist_directory
        self._embedding_function = embedding_function or embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the ChromaDB client.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self._persist_directory, exist_ok=True)
            
            # Initialize client
            self._client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            self._initialized = True
            logger.info("ChromaDB client initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            return False
    
    async def create_collection(self, collection_name: str) -> bool:
        """
        Create a new collection in ChromaDB.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if collection exists
            try:
                self._client.get_collection(name=collection_name)
                logger.info(f"ChromaDB collection {collection_name} already exists")
            except:
                # Create collection
                self._client.create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function
                )
                logger.info(f"Created ChromaDB collection: {collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating ChromaDB collection {collection_name}: {str(e)}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from ChromaDB.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting ChromaDB collection {collection_name}: {str(e)}")
            return False
    
    async def list_collections(self) -> List[str]:
        """
        List all collections in ChromaDB.
        
        Returns:
            List of collection names
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            collections = self._client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Error listing ChromaDB collections: {str(e)}")
            return []
    
    async def insert(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Insert documents into a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            texts: List of text documents to insert
            metadata: List of metadata dictionaries for each document
            ids: Optional list of IDs for the documents (generated if not provided)
            
        Returns:
            List of inserted document IDs
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # Get collection
            collection = self._client.get_collection(name=collection_name)
            
            # Add documents
            collection.add(
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Inserted {len(texts)} documents into ChromaDB collection {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Error inserting into ChromaDB collection {collection_name}: {str(e)}")
            return []
    
    async def search(
        self, 
        collection_name: str, 
        query: str, 
        limit: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents in a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            query: Search query
            limit: Maximum number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results with document ID, text, metadata, and score
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get collection
            collection = self._client.get_collection(name=collection_name)
            
            # Query collection
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": results["distances"][0][i] if "distances" in results else None
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching ChromaDB collection {collection_name}: {str(e)}")
            return []
    
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete documents from a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get collection
            collection = self._client.get_collection(name=collection_name)
            
            # Delete documents
            collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from ChromaDB collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB collection {collection_name}: {str(e)}")
            return False
    
    async def get(self, collection_name: str, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get documents by ID from a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to retrieve
            
        Returns:
            List of documents with ID, text, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get collection
            collection = self._client.get_collection(name=collection_name)
            
            # Get documents
            results = collection.get(ids=ids)
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error fetching from ChromaDB collection {collection_name}: {str(e)}")
            return []


class VectorDBFactory:
    """Factory for creating vector database clients."""
    
    @staticmethod
    def create_client(db_type: str, **kwargs) -> VectorDBClient:
        """
        Create a vector database client.
        
        Args:
            db_type: Type of vector database ("pinecone" or "chromadb")
            **kwargs: Additional arguments for the client
            
        Returns:
            Vector database client
        """
        if db_type.lower() == "pinecone":
            return PineconeClient(**kwargs)
        elif db_type.lower() == "chromadb":
            return ChromaDBClient(**kwargs)
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")
