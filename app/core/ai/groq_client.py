import json
import re

import httpx
from groq import AsyncGroq
from groq import BadRequestError as GroqBadRequestError

from app.core.ai.base import BaseAIClient, ToolCallResult
from app.core.exceptions import ServiceUnavailableException


def _reconstruct_fallback_args(raw_content: str, tool_name: str, tools: list[dict]) -> dict:
    """
    llama-3.3-70b sometimes emits just the value (e.g. an array) between XML tags
    instead of the full JSON arguments object. Reconstruct the proper dict by
    wrapping the value in the first required parameter from the tool schema.
    """
    parsed = json.loads(raw_content)
    if isinstance(parsed, dict):
        return parsed
    for tool in tools:
        if tool.get("function", {}).get("name") == tool_name:
            required = tool["function"]["parameters"].get("required", [])
            if required:
                return {required[0]: parsed}
    return {"result": parsed}


class GroqAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str):
        self._model = model
        self._client = AsyncGroq(
            api_key=api_key,
            http_client=httpx.AsyncClient(verify=False),
        )

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict,
        max_tokens: int = 4096,
    ) -> ToolCallResult:
        try:
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
        except GroqBadRequestError as exc:
            # llama-3.3-70b falls back to <function=name>[...]</function> XML format
            try:
                body = exc.response.json()
                failed_gen: str = body.get("error", {}).get("failed_generation", "")
                match = re.search(r"<function=(\w+)>(.*?)</function>", failed_gen, re.DOTALL)
                if not match:
                    raise ServiceUnavailableException("AI generation failed. Please try again.")
                tool_name = match.group(1)
                arguments = _reconstruct_fallback_args(match.group(2).strip(), tool_name, tools)
                return ToolCallResult(tool_name=tool_name, arguments=arguments)
            except (ValueError, AttributeError):
                raise ServiceUnavailableException("AI generation failed. Please try again.")
