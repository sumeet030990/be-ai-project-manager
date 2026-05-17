from app.core.ai.base import BaseAIClient

_PROVIDER_DEFAULTS: dict[str, str] = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "groq": "llama-3.3-70b-versatile",
    "deepseek": "deepseek-chat",
}


def get_ai_client_for_provider(provider: str, api_key: str, model: str) -> BaseAIClient:
    if provider == "claude":
        from app.core.ai.claude_client import ClaudeAIClient
        return ClaudeAIClient(api_key=api_key, model=model)
    if provider == "openai":
        from app.core.ai.openai_client import OpenAIAIClient
        return OpenAIAIClient(api_key=api_key, model=model)
    if provider == "groq":
        from app.core.ai.groq_client import GroqAIClient
        return GroqAIClient(api_key=api_key, model=model)
    if provider == "deepseek":
        from app.core.ai.deepseek_client import DeepSeekAIClient
        return DeepSeekAIClient(api_key=api_key, model=model)
    raise ValueError(f"Unsupported AI provider: {provider}")
