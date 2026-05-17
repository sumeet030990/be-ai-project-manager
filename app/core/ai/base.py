from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolCallResult:
    tool_name: str
    arguments: dict


class BaseAIClient(ABC):
    @abstractmethod
    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict,
        max_tokens: int = 4096,
    ) -> ToolCallResult:
        ...
