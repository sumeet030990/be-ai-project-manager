import uuid

import httpx
from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.base import BaseAIClient
from app.core.ai.factory import get_ai_client_for_provider
from app.core.config import settings

_FALLBACK_GROQ_MODEL = "llama-3.3-70b-versatile"

_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    """Legacy singleton Groq client (env-key fallback). Prefer get_project_ai_client()."""
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            http_client=httpx.AsyncClient(verify=False),
        )
    return _groq_client


async def get_project_ai_client(
    project_id: uuid.UUID,
    session: AsyncSession,
    config_id: uuid.UUID | None = None,
) -> BaseAIClient:
    """
    Return the active AI client for the given project.
    If config_id is provided, uses that specific config.
    Otherwise uses the project's default config from the DB.
    Falls back to the env Groq key if no config is found.
    """
    from app.core.ai.groq_client import GroqAIClient
    from app.core.encryption import decrypt_api_key
    from app.repositories.project_ai_config_repository import ProjectAIConfigRepository

    repo = ProjectAIConfigRepository(session)
    if config_id is not None:
        config = await repo.get_by_project_and_id(project_id, config_id)
    else:
        config = await repo.get_default_for_project(project_id)

    if config is None:
        return GroqAIClient(api_key=settings.GROQ_API_KEY, model=_FALLBACK_GROQ_MODEL)

    decrypted_key = decrypt_api_key(config.api_key)
    return get_ai_client_for_provider(config.provider, decrypted_key, config.model_name)
