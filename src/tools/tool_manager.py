from os import path
import json
import inspect
from importlib.machinery import SourceFileLoader
from typing import Callable
import logging

class ToolManager:

    def __call__(self, name: str, args: dict):
        return self.call(name, args)

    def __init__(self):
        self.tools = []
        self.tool_func: dict[str, Callable] = {}
        self.root_path = path.abspath(path.join("src", "tools"))
        self.initialize_tools()
    
    def initialize_tools(self):
        tools_path = path.abspath(path.join('src', 'tools.json'))
        tools: dict = {}
        with open(tools_path, "r", encoding="utf-8") as fs:
            tools = json.load(fs)
        
        meta = tools.get('meta')
        if not meta:
            raise Exception("工具元数据为空！")
        self.tools = tools.get('tools', [])

        modules = meta.get('modules', [])
        self.__init_modules(modules)
    
    def __init_modules(self, modules: list[str]):
        for module_name in modules:
            temp_module_name = module_name
            if not temp_module_name.endswith('.py'):
                temp_module_name += '.py'
            module_path = path.join(self.root_path, "modules", temp_module_name)

            if not path.exists(module_path):
                raise Exception(f"找不到模块'{module_path}'")
            module = SourceFileLoader(module_name, module_path).load_module()
            functions = inspect.getmembers(module, inspect.isfunction)
            for (name, func) in functions:
                logging.info(
                    f"加载工具 '{module_name}.{name}'"
                )
                self.tool_func[f"{module_name}.{name}"] = func
    
    def get_tools_schema(self):
        return self.tools
    
    def call(self, name: str, args: dict):
        if len(name.split('.')) != 2:
            return {
                "message": "请严格按照 'module.tool_name' 的格式调用工具",
                "data": None
            }
        
        # 参数校验
        # for tool in self.tools:
        #     if tool['function']["name"] != name:
        #         continue
        #     properties: dict = tool['function']["parameters"]['properties']
        #     for property in properties:
                
        #         if property['type']
        #     break
        
        tool_fun = self.tool_func.get(name)
        if tool_fun == None:
            return {
                "message": f"调用失败，程序没有名为'{name}'的工具",
                "data": None
            }
        
        return self.tool_func[name](**args)


