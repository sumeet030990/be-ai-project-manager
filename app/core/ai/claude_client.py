import anthropic

from app.core.ai.base import BaseAIClient, ToolCallResult
from app.core.exceptions import ServiceUnavailableException


class ClaudeAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str):
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Anthropic tool format."""
        result = []
        for tool in tools:
            fn = tool["function"]
            result.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn["parameters"],
            })
        return result

    def _convert_tool_choice(self, tool_choice: str | dict) -> dict:
        if isinstance(tool_choice, str):
            return {"type": "auto"} if tool_choice == "auto" else {"type": "any"}
        # {"type": "function", "function": {"name": "..."}}
        return {"type": "tool", "name": tool_choice["function"]["name"]}

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict,
        max_tokens: int = 4096,
    ) -> ToolCallResult:
        system_msg = None
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_messages.append(m)

        kwargs: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            tools=self._convert_tools(tools),
            tool_choice=self._convert_tool_choice(tool_choice),
            messages=user_messages,
        )
        if system_msg:
            kwargs["system"] = system_msg

        response = await self._client.messages.create(**kwargs)

        for block in response.content:
            if block.type == "tool_use":
                return ToolCallResult(tool_name=block.name, arguments=block.input)

        raise ServiceUnavailableException("AI did not return a structured response. Please try again.")
