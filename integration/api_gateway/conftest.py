import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the API directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../api"))

# This will be used by the actual tests
@pytest.fixture
def test_client():
    from main import app
    return TestClient(app)

# Mock services for testing
class MockLLMService:
    def generate(self, prompt, max_tokens=100, temperature=0.7):
        return {
            "text": f"Mock response for: {prompt}",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(prompt.split()) + 10
            }
        }

class MockEmbeddingService:
    def create_embedding(self, texts):
        return {
            "embeddings": [
                [0.1, 0.2, 0.3, 0.4, 0.5] for _ in texts
            ],
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in texts),
                "total_tokens": sum(len(text.split()) for text in texts)
            }
        }

class MockMemoryService:
    def store(self, content, metadata):
        return {
            "id": "mem_123456789",
            "status": "success",
            "timestamp": "2025-05-23T10:15:00Z"
        }
    
    def retrieve(self, query, limit=10):
        return [
            {
                "id": f"mem_{i}",
                "content": f"Mock memory related to: {query}",
                "metadata": {"relevance": 0.9 - (i * 0.1), "timestamp": "2025-05-23T10:15:00Z"},
            }
            for i in range(min(3, limit))
        ]

class MockToolsService:
    def list_tools(self):
        return [
            {
                "id": "web_search",
                "name": "Web Search",
                "description": "Search the web for information",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"}
                }
            },
            {
                "id": "calculator",
                "name": "Calculator",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
                }
            }
        ]
    
    def execute_tool(self, tool_id, parameters):
        if tool_id == "web_search":
            return {
                "result": f"Mock search results for: {parameters.get('query', 'unknown query')}",
                "status": "success"
            }
        elif tool_id == "calculator":
            return {
                "result": f"Mock calculation result for: {parameters.get('expression', '1+1')}",
                "status": "success"
            }
        else:
            raise ValueError(f"Tool {tool_id} not found")

@pytest.fixture
def mock_llm_service():
    return MockLLMService()

@pytest.fixture
def mock_embedding_service():
    return MockEmbeddingService()

@pytest.fixture
def mock_memory_service():
    return MockMemoryService()

@pytest.fixture
def mock_tools_service():
    return MockToolsService()
