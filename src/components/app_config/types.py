import typing

# 大模型配置
class LLMOption(typing.TypedDict):
    name: str
    key_name: str
    base_url: str

class LLMConfig(typing.TypedDict):
    default: str
    models: dict[str, LLMOption]

# 日志配置
class LoggingHandlerOptions:
    type: typing.Literal["console", "file"]
    format: str

class LoggingOption:
    default: str
    handlers: dict[str, LoggingHandlerOptions]

# 能力配置
## mcp

class AuthOption(typing.TypedDict):
    callback_url: str
    redirect_uris: list[str]

class MCPStreamableHTTP(typing.TypedDict):
    enable: bool
    url: str
    desc: str
    headers: dict[str, str] | None
    auth_option: AuthOption | None

class MCPStdio(typing.TypedDict):
    enable: bool
    cmd: str
    desc: str
    args: list[str]
    env: dict[str, str] | None

class MCPOption(typing.TypedDict):
    enable: bool
    servers: dict[str, typing.Union[MCPStreamableHTTP, MCPStdio]] | None

## skills
class SkillsOption(typing.TypedDict):
    enable: bool
    base_path: str

class Capabilities(typing.TypedDict):
    mcp: MCPOption
    skills: SkillsOption

# 顶级配置结构
class AppConfigOption(typing.TypedDict):
    logging: typing.Any
    llm: LLMConfig
    capabilities: Capabilities
