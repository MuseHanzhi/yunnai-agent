from typing import (
    TypedDict,
    Literal,
    Union,
    Any
)

# 大模型配置
class LLMOption(TypedDict):
    name: str
    key_name: str
    base_url: str
    stream: bool | None

class LLMConfigOption(TypedDict):
    default: str
    models: dict[str, LLMOption]

# 日志配置
class LoggingHandlerOptions(TypedDict):
    type: Literal["console", "file"]
    log_path: str | None
    format: str

class LoggingOption(TypedDict):
    default: str
    handlers: dict[str, list[LoggingHandlerOptions]]

# 系统配置

class ReconnectOption(TypedDict):
    enable: bool
    try_interval: int
    max_retry: int

class IPCOption(TypedDict):
    enable: bool
    uri: str
    reconnect: ReconnectOption

class SysInfo(TypedDict):
    name: str
    version: str
    

class SystemOption(TypedDict):
    require_env: list[str]
    thread_workers: int | None
    system_prompt_path: str | None
    sys_info: SysInfo
    ipc: IPCOption

# 能力配置
## mcp

class AuthOption(TypedDict):
    callback_url: str
    redirect_uris: list[str]

class MCPStreamableHTTPOption(TypedDict):
    enable: bool
    url: str
    desc: str
    headers: dict[str, str] | None
    auth_option: AuthOption | None

class MCPStdioOption(TypedDict):
    enable: bool
    cmd: str
    desc: str
    args: list[str]
    env: dict[str, str] | None

class MCPOption(TypedDict):
    auto_inject: bool
    enable: bool
    servers: dict[str, Union[MCPStreamableHTTPOption, MCPStdioOption]] | None

## skills
class SkillsOption(TypedDict):
    auto_inject: bool
    enable: bool
    base_path: str

class CapabilitiesConfigOption(TypedDict):
    mcp: MCPOption
    skills: SkillsOption

# 插件配置
class PluginOption(TypedDict):
    module_path: str
    class_name: str | None

class PluginConfigOption(TypedDict):
    search_path: str

# 顶级配置结构
class AppConfigOption(TypedDict):
    logging: Any
    system: SystemOption
    llm: LLMConfigOption
    capabilities: CapabilitiesConfigOption
    plugin_config: PluginConfigOption
