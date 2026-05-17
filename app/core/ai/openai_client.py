import json

from openai import AsyncOpenAI

from app.core.ai.base import BaseAIClient, ToolCallResult
from app.core.exceptions import ServiceUnavailableException


class OpenAIAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self._model = model
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict,
        max_tokens: int = 4096,
    ) -> ToolCallResult:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            messages=messages,
        )
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ServiceUnavailableException("AI did not return a structured response. Please try again.")
        tc = tool_calls[0]
        return ToolCallResult(
            tool_name=tc.function.name,
            arguments=json.loads(tc.function.arguments),
        )
