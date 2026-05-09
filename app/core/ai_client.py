import httpx
from groq import AsyncGroq

from app.core.config import settings

_client: AsyncGroq | None = None


def get_ai_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            http_client=httpx.AsyncClient(verify=False),
        )
    return _client
