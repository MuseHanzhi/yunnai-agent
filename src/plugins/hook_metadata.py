from typing import Callable

from .plugin import Hooks, Plugin

class HookMetadata:

    def __init__(self, hook_name: Hooks, hook_func: Callable, plugin: Plugin):
        self.hook_func = hook_func
        self.hook_name: Hooks = hook_name
        self.plugin = plugin
        self.enable = True
    def run(self, *args, **arguments):
        self.hook_func(self.plugin, *args, **arguments)