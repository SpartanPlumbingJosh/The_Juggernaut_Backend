from fastapi import APIRouter

from routes.auth import router as auth_router
from routes.llm import router as llm_router
from routes.embedding import router as embedding_router
from routes.memory import router as memory_router
from routes.tools import router as tools_router
from routes.orchestrator import router as orchestrator_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(llm_router, prefix="/llm", tags=["LLM Service"])
api_router.include_router(embedding_router, prefix="/embedding", tags=["Embedding Service"])
api_router.include_router(memory_router, prefix="/memory", tags=["Memory Service"])
api_router.include_router(tools_router, prefix="/tools", tags=["Tools Service"])
api_router.include_router(orchestrator_router, prefix="/orchestrator", tags=["Orchestrator"])
