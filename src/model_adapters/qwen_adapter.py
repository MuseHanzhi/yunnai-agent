from src.components.ai_chat.chat_state import ChatState

from src.components.ai_chat.base_adapter import BaseAdapter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.components.ai_chat.chat_state import ChatState

class QwenAdapter(BaseAdapter):
    def thinking_mode(self, state: ChatState, mode: bool):
        state.set_extra_body("enable_thinking", mode)