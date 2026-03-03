from typing import TypedDict, NotRequired, Required

class ServiceConfig(TypedDict):
    base_url: Required[str]
    model_name: Required[str]

class EnvOptions(TypedDict):
    lang: NotRequired[str | None]
    device: NotRequired[str | None]
    network: NotRequired[str | None]
    cpu: NotRequired[str | None]
    