import typing

# 大模型配置
class LLMOption(typing.TypedDict):
    name: str
    key_name: str
    base_url: str
    stream: bool | None

class LLMConfigOption(typing.TypedDict):
    default: str
    models: dict[str, LLMOption]

# 日志配置
class LoggingHandlerOptions(typing.TypedDict):
    type: typing.Literal["console", "file"]
    log_path: str | None
    format: str

class LoggingOption(typing.TypedDict):
    default: str
    handlers: dict[str, list[LoggingHandlerOptions]]

# 系统配置

class SysInfo(typing.TypedDict):
    name: str
    version: str

class IPCOption(typing.TypedDict):
    protocol: str
    host: str
    port: int
    

class SystemOption(typing.TypedDict):
    ipc_option: IPCOption | None
    require_env: list[str]
    thread_workers: int | None
    system_prompt_path: str | None
    sys_info: SysInfo

# 能力配置
## mcp

class AuthOption(typing.TypedDict):
    callback_url: str
    redirect_uris: list[str]

class MCPStreamableHTTPOption(typing.TypedDict):
    enable: bool
    url: str
    desc: str
    headers: dict[str, str] | None
    auth_option: AuthOption | None

class MCPStdioOption(typing.TypedDict):
    enable: bool
    cmd: str
    desc: str
    args: list[str]
    env: dict[str, str] | None

class MCPOption(typing.TypedDict):
    enable: bool
    servers: dict[str, typing.Union[MCPStreamableHTTPOption, MCPStdioOption]] | None

## skills
class SkillsOption(typing.TypedDict):
    enable: bool
    base_path: str

class CapabilitiesConfigOption(typing.TypedDict):
    mcp: MCPOption
    skills: SkillsOption

# 插件配置
class PluginOption(typing.TypedDict):
    module_path: str
    class_name: str | None

class PluginConfigOption(typing.TypedDict):
    base_module: str
    plugins: list[PluginOption]

# 顶级配置结构
class AppConfigOption(typing.TypedDict):
    logging: typing.Any
    system: SystemOption
    llm: LLMConfigOption
    capabilities: CapabilitiesConfigOption
    plugin_config: PluginConfigOption
