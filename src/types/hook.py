from typing import TypedDict
from .lfecycle_hooks import Hooks

class Hook(TypedDict):
    trigger_order: int
    hook_name: Hooks
