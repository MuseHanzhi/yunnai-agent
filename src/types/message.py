from typing import (
    TypedDict,
    Required,
    NotRequired
)

class ModelOptions(TypedDict):
    model_name: Required[str]
    think_mode: Required[bool]

class MessageDataOptions(TypedDict):
    filePaths: NotRequired[list[str]]
    text: Required[str]

class MessageOptions(TypedDict):
    options: Required[ModelOptions]
    data: Required[MessageDataOptions]
