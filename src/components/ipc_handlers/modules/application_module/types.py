from typing import TypedDict, Literal

class ModelOptions(TypedDict):
    model_name: str
    think_mode: bool

class MessageDataOptions(TypedDict):
    filePaths: list[str]
    text: str

class MessageOptions(TypedDict):
    message: str
    type: Literal["user", "system"]