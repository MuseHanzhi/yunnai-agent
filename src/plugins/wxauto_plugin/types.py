from typing import (
    TypedDict,
    Literal,
    Any
)

class OSSOption(TypedDict):
    region: str
    bucket: str

class AgentPromptPathOption(TypedDict):
    chat: str

class AgentOption(TypedDict):
    word_delay: float
    prompt_path: AgentPromptPathOption

class ListenOption(TypedDict):
    metadata: dict | None
    nickname: str
    event_type: str
    msg_type: list[Literal["time", "text", "quote", "voice", "image", "video", "file", "location", "link", "emotion", "merge", "personal_card", "note", "order"]]

class Config(TypedDict):
    required_env: list[str]
    oss: OSSOption
    agent: AgentOption
    listen: list[ListenOption]
