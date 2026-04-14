from src.components.ai_chat.chat_state import ChatState

from src.components.ai_chat.base_adapter import BaseAdapter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.components.ai_chat.chat_state import ChatState

class DoubaoAdapter(BaseAdapter):
    def thinking_mode(self, state: ChatState, mode):
        mode_value = "auto"
        if mode == True:
            mode_value = "enabled"
        elif mode == False:
            mode_value = "disabled"
        state.set_extra_body("thinking", {
            "type": mode_value
        })