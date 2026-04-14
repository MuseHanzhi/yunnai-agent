from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_state import ChatState

class BaseAdapter(ABC):
    @abstractmethod
    def thinking_mode(self, state: "ChatState", mode): ...