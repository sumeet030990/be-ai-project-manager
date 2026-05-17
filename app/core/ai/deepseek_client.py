from app.core.ai.openai_client import OpenAIAIClient

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekAIClient(OpenAIAIClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key=api_key, model=model, base_url=_DEEPSEEK_BASE_URL)
