from src.components.logger.logger import LogCreator
from src.components.app_config.types import PluginConfigOption, PluginOption
from src.plugins.plugin import (
    Plugin,
    Hooks
)
import importlib

logger = LogCreator.instance.create(__name__)

class PluginManager:
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.hook_registry_map: dict[Hooks, list[Plugin]] = {}
    
    def initialize(self, config: PluginConfigOption):
        base_module = config["base_module"].strip(".")
        plugins: list[PluginOption] = config.get("plugins", [])
        for plugin in plugins:
            module_path = ".".join([base_module, plugin["module_path"].strip(".")])
            logger.info(f"开始加载插件: {module_path}")

            module = importlib.import_module(module_path)
            # 实例化插件
            plugin_class_instance: Plugin
            try:
                plugin_class_name = plugin.get("class_name")
                if not plugin_class_name:   # 没有绑定类名则直接用主模块的目录作为插件类名
                    plugin_class_name = "".join([f"{item[0].upper()}{item[1:]}" for item in module_path.split(".")[-2].split("_") if item])
                plugin_class_instance = getattr(module, plugin_class_name)()
            except TypeError:
                logger.warning(f"插件类'{plugin_class_name}'找不到无参构造函数 - 跳过加载")
                continue
            except IndexError:
                logger.warning(f"插件插件模块路径'{module_path}'无效 - 跳过加载")
                continue

            # 被后来的同名插件覆盖
            if plugin_class_instance.name in self.plugins:
                logger.warning(f"插件 '{plugin_class_instance.name}'名称与其他插件名称冲突，跳过加载")

            # 注册hook与移除冲突的插件Hook
            for hook_name in plugin_class_instance.hook_registry:
                if hook_name in self.hook_registry_map:
                    self.hook_registry_map[hook_name].append(plugin_class_instance)
                else:
                    self.hook_registry_map[hook_name] = [plugin_class_instance]
            
            # 注册插件
            self.plugins[plugin_class_instance.name] = plugin_class_instance
            logger.info(f"插件'{module_path}'加载完成")
            
    
    def remove(self, target: str | Plugin):
        if target not in self.plugins:
            return
        
        if isinstance(target, str):
            target = self.plugins.pop(target)
        elif isinstance(target, Plugin):
            self.plugins.pop(target.name)
        else:
            return
        
        try:
            target.deinit()
        except Exception as ex:
            logger.error(f"插件'{target.name}'移除时出现异常", exc_info=ex)

        # 移除hook
        for hook in target.hook_registry:
            if hook not in self.hook_registry_map:
                continue
            self.hook_registry_map[hook].remove(target)
            if not self.hook_registry_map[hook]:
                self.hook_registry_map.pop(hook)
    
    def get_plugin(self, name: str) -> None | Plugin:
        return self.plugins.get(name)

    def emit(self, plugin_name: str, name: str, arguments: dict = {}):
        plugin = self.plugins.get(plugin_name)
        if plugin is None:
            raise Exception(f"没有名为 '{plugin_name}' 的插件")
        plugin.emit(name, arguments)


    def trigger(self, hook_name: Hooks, **arguments):
        hooks = self.hook_registry_map.get(hook_name, [])
        for plugin in hooks:
            try:
                getattr(plugin, hook_name)(**arguments)
            except Exception as err:
                logger.error(f"触发插件'{plugin.name}' Hook '{hook_name}'时发生异常", exc_info=err)
