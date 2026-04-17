from typing import TypedDict

class ReconnectOption(TypedDict):
    enable: bool
    try_interval: int
    max_retry: int

class IPCOption(TypedDict):
    protocol: str
    host: str
    port: int
    reconnect: ReconnectOption