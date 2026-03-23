from typing import (
    TypedDict,
    Required,
    Literal
)

class ChangeModelOption(TypedDict):
    model: str
    prompt_name: Required[Literal["agent", "chat", "model_router"]]
