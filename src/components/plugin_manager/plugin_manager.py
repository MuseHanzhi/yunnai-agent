import os
import importlib
import inspect

import yaml

from src.plugins.hook_metadata import HookMetadata
from src.plugins.plugin import Plugin, PluginInfo
from src.components.logger.logger import LogCreator
from src.components.app_config.types import PluginConfigOption
from src.plugins.plugin import (
    Plugin,
    Hooks
)

from .types import PluginManifest, IPCTiming

from typing import (
    Any
)

logger = LogCreator.instance.create(__name__)
class PluginManager:

    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.ipc_before_hooks: dict[str, list[HookMetadata]] = {}
        self.ipc_after_hooks: dict[str, list[HookMetadata]] = {}
    
    def _load_manifest(self, manifest_path: str) -> PluginManifest:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def load_plugin(self, model_path: str, manifest: PluginManifest):
        if manifest["name"] in self.plugins:
            raise Exception(f"插件'{manifest['name']}'与已注册的插件名称冲突")

        entry_script, entry_class = manifest["entry"].split(".")

        entry_module = model_path+"."+entry_script
        plugin_module = importlib.import_module(entry_module)
        plugin_instance: Plugin
        plugin_class: Any = getattr(plugin_module, entry_class)
        try:
            plugin_class = getattr(plugin_module, entry_class)
            plugin_instance = plugin_class()
            plugin_instance.info = PluginInfo(
                name=manifest["name"],
                author=manifest["author"],
                version=manifest["version"],
                description=manifest["description"]
            )
        except TypeError as err:
            raise Exception(f"插件'{manifest['name']}'入口类'{entry_class}'无法实例化") from err
        
        for _, method in inspect.getmembers(plugin_class, inspect.isfunction):
            hook_name: Hooks | None = getattr(method, "_hook_name", None)
            timing: IPCTiming | None = getattr(method, "_hook_timing", None)
            if not hook_name or not timing:
                continue
            hook = HookMetadata(hook_name, method, plugin_instance)
            if timing == "before":
                self.ipc_before_hooks.setdefault(hook_name, []).append(hook)
            elif timing == "after":
                self.ipc_after_hooks.setdefault(hook_name, []).append(hook)
            else:
                raise Exception(f"插件'{manifest['name']}'的Hook '{hook_name}'的 timing 参数错误, 仅支持 'before' 和 'after'")
            self.plugins[plugin_instance.info.name] = plugin_instance
        logger.debug(f"加载插件'{manifest['name']}'成功")
    
    def initialize(self, config: PluginConfigOption):
        search_path = config["search_path"]
        plugin_root_path = os.path.join(os.getcwd(), search_path)
        model_root = search_path.strip(".").strip("/").strip("\\").replace("/", ".").replace("\\", ".")
        plugin_dirs = os.listdir(plugin_root_path)
        for plugin_dir in plugin_dirs:
            plugin_path = os.path.join(plugin_root_path, plugin_dir)
            if not plugin_dir.endswith("_plugin") or not os.path.isdir(plugin_path):
                continue
            manifest_path = os.path.join(plugin_path, "manifest.yaml")
            if not os.path.exists(manifest_path):
                continue
            try:
                manifest = self._load_manifest(manifest_path)
                self.load_plugin(model_root+"."+plugin_dir, manifest)
            except Exception as err:
                logger.error(f"加载插件'{plugin_path}'时发生异常", exc_info=err)
    
    def enable(self, plugin: str | Plugin, state: bool):
        if plugin not in self.plugins:
            raise Exception(f"没有名为 '{plugin}' 的插件")
        if isinstance(plugin, str):
            target = self.plugins[plugin]
        elif isinstance(plugin, Plugin):
            target = plugin
        else:
            return
        target.enable = state

    def remove(self, plugin: str | Plugin):
        if plugin not in self.plugins:
            raise Exception(f"没有名为 '{plugin}' 的插件")
        
        if isinstance(plugin, str):
            target = self.plugins[plugin]
        elif isinstance(plugin, Plugin):
            target = plugin
        else:
            return

        try:
            target.deinit()
        except Exception as ex:
            raise Exception(f"插件'{target.info.name}'无法正常卸载") from ex

        # 移出注册表
        self.plugins.pop(target.info.name)
        # 移除hooks
        for key, hooks in self.ipc_before_hooks.items():
            self.ipc_before_hooks[key] = [h for h in hooks if h.plugin.info.name != target.info.name]

        for key, hooks in self.ipc_after_hooks.items():
            self.ipc_after_hooks[key] = [h for h in hooks if h.plugin.info.name != target.info.name]
    
    def get_plugin(self, name: str) -> None | Plugin:
        return self.plugins.get(name)

    def emit(self, plugin_name: str, name: str, arguments: dict = {}) -> Any:
        plugin = self.plugins.get(plugin_name)
        if plugin is None:
            raise Exception(f"没有名为 '{plugin_name}' 的插件")
        return plugin.emit(name, arguments)


    def trigger(self, hook_name: Hooks, ipc_timing: IPCTiming, *args, **arguments):
        if ipc_timing == "before":
            hooks = self.ipc_before_hooks.get(hook_name, [])
        elif ipc_timing == "after":
            hooks = self.ipc_after_hooks.get(hook_name, [])
        else:
            raise Exception(f"Hook '{hook_name}' 的 timing 参数错误, 仅支持 'before' 和 'after'")

        for hook in hooks:
            if not hook.enable:
                continue
            try:
                hook.run(*args, **arguments)
            except Exception as err:
                logger.error(f"触发插件'{hook.plugin.info.name}' Hook '{hook_name}'时发生异常", exc_info=err)
