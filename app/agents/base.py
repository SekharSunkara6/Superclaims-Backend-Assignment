from abc import ABC, abstractmethod


class BaseAgent(ABC):
    @abstractmethod
    async def parse(self, text: str) -> dict:
        ...
