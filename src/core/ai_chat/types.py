from typing import (
    TypedDict,
    NotRequired,
    Required,
    Literal
)

class ServiceConfig(TypedDict):
    base_url: Required[str]
    api_key: NotRequired[str]

class EnvOptions(TypedDict):
    lang: NotRequired[str | None]
    device: NotRequired[str | None]
    network: NotRequired[str | None]
    cpu: NotRequired[str | None]

class ToolMessage(TypedDict):
    role: Literal["tool"]
    id: str
    name: str
    result: str
    desc: str

class ChatMessage(TypedDict):
    role: Literal["assistant", "user", "tool", "system", "develop"]
    content: str

class ToolPropertySchema:
    type: Literal["string", "number", "boolean", "object", "array"]
    desc: str

class ToolParams(TypedDict):
    type: Literal["object"]
    properties: dict[str, ToolPropertySchema]
    required: list[str]

class Tool(TypedDict):
    name: str
    desc: str
    params: ToolParams
