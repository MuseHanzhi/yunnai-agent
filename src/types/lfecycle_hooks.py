from typing import Literal

Hooks = Literal[
    "on_app_before_initialize",
    "on_app_after_initialized",
    "on_llm_response",
    "on_app_will_close",
    "on_message_before_send",
    "on_message_after_sended",
    "on_ready"
]