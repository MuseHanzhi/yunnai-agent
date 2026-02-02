from typing import MutableMapping
from plugins import Plugin
import logging

class PluginManager(MutableMapping[str, Plugin]):
    def __delitem__(self, key: str) -> None:
        del self.plugins[key]

    def __iter__(self):
        return self.plugins.__iter__()

    def __len__(self):
        return len(self.plugins)
        
    def __getitem__(self, name) -> Plugin | None:
        return self.plugins.get(name)
    
    def __setitem__(self, key: str, value: Plugin) -> None:
        self.plugins[key] = value

    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
    
    def init(self):
        for (name, plugin) in self.plugins.items():
            try:
                plugin.init()
            except Exception as e:
                logging.warning(f"插件 '{name}' 初始化出现异常: {e}")

    def add(self, *plugins: Plugin):
        for plugin in plugins:
            if plugin.name in self.plugins:
                logging.warning(f"插件 '{plugin.name}' 被覆盖")
            self.plugins[plugin.name] = plugin
    
    def remove(self, plugin: str | Plugin):
        if isinstance(plugin, str) and plugin in self.plugins:
            target = self.plugins.pop(plugin)
            target.set_state(False)
        elif isinstance(plugin, Plugin):
            self.plugins.pop(plugin.name)
            plugin.set_state(False)
    
    def set_plugin_state(self, name: str, state: bool):
        plugin = self.plugins.get(name)
        if not plugin:
            raise ValueError(f"没有名为'{name}'的插件")
        plugin.set_state(state)
    
    def get_plugin(self, name: str) -> None | Plugin:
        return self.plugins.get(name)

    def trigger(self, timming: str, **arguments):
        for _, plugin in self.plugins.items():
            if not plugin.state:
                continue
            if timming == "on_app_before_initialize":   # 应用初始化前
                plugin.on_app_before_initialize(**arguments)
                continue
            if timming == "on_app_after_initialized":   # 应用初始化后
                plugin.on_app_after_initialized(**arguments)
                continue
            if timming == "on_ai_reply":                # 智能体回复
                plugin.on_ai_reply(**arguments)
                continue
            if timming == "on_ai_reply_completed":      # 智能体回复完毕
                plugin.on_ai_reply_completed(**arguments)
                continue
            if timming == "on_app_will_close":          # 应用将关闭
                plugin.on_app_will_close(**arguments)
                continue
            if timming == "on_message_before_send":     # 信息发送前
                plugin.on_message_before_send(**arguments)
                continue
            if timming == "on_message_after_sended":    # 信息发送后
                plugin.on_message_after_sended(**arguments)
                continue
            if timming == "on_background_thread_start": # 后台线程启动前
                plugin.on_background_thread_start(**arguments)
                continue
            if timming == "on_background_thread_end":   # 后台线程结束
                plugin.on_background_thread_end(**arguments)
                continue
            if timming == "on_window_hide":             # 窗体隐藏/关闭
                plugin.on_window_hide(**arguments)
                continue
            if timming == "on_window_minimize":         # 窗体最小化
                plugin.on_window_minimize(**arguments)
                continue
            if timming == "on_window_maximize":         # 窗体最大化
                plugin.on_window_maximize(**arguments)
                continue
            if  timming == "on_main_window_show":       # 窗体显示/打开
                plugin.on_main_window_show(**arguments)


