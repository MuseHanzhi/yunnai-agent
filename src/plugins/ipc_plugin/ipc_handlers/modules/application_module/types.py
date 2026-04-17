from typing import TypedDict

class ModelOptions(TypedDict):
    model_name: str
    think_mode: bool

class MessageDataOptions(TypedDict):
    filePaths: list[str]
    text: str

class MessageOptions(TypedDict):
    options: ModelOptions
    data: MessageDataOptions