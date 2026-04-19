from typing import TypedDict
from src.plugins.plugin import IPCTiming

class PluginManifest(TypedDict):
    description: str
    name: str
    author: str
    version: str
    entry: str
