from typing import TypedDict, NotRequired, Required

class ServiceConfig(TypedDict):
    api_key: Required[str]
    base_url: NotRequired[str | None]

class EnvOptions(TypedDict):
    lang: NotRequired[str | None]
    device: NotRequired[str | None]
    network: NotRequired[str | None]
    cpu: NotRequired[str | None]