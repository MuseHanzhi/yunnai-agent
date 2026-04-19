import re
import os
import httpx
import asyncio
from typing import (
    Union,
    Literal,
    Callable,
    TYPE_CHECKING
)
from urllib.parse import parse_qs, urlparse
from pydantic import AnyUrl

from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientMetadata
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.components.app_config.types import (
    MCPStdioOption,
    MCPStreamableHTTPOption
)
from .in_memory_token_storage import InMemoryTokenStorage
from src.components.logger.logger import LogCreator

if TYPE_CHECKING:
    from .types import (
        ClientInfo
    )

OnConnectedHandler = Callable[[], None]
OnConnectErrorHandler = Callable[[Exception], None]
logger = LogCreator().instance.create(__name__)
class MCPClient:
    def __init__(self, client_info: "ClientInfo", config: Union[MCPStdioOption, MCPStreamableHTTPOption]):
        self.session: ClientSession | None = None
        self.client_future: asyncio.Future | None = None
        self.config = config
        self.client_info = client_info
        self.on_connected: OnConnectedHandler | None = None
        self.on_connect_error: OnConnectErrorHandler | None = None
    
    @staticmethod
    async def handle_redirect(auth_url: str) -> None:
        logger.debug(f"redirected: {auth_url}")
    
    async def connect_streamable_http(self, config: MCPStreamableHTTPOption):
        auth_option = config.get("auth_option")
        if auth_option:
            await self.auth_connect(config)
            return
        
        headers = config.get("headers")
        if headers:
            headers = self.replace_env_key(headers)
        is_exception = False
        try:
            async with httpx.AsyncClient(headers=headers) as http_client:
                try:
                    async with streamable_http_client(config["url"], http_client=http_client) as (read, write, _):
                        try:
                            async with ClientSession(read, write) as session:
                                try:
                                    self.session = session
                                    await self.session.initialize()
                                except Exception as ex:
                                    if self.on_connect_error:
                                        self.on_connect_error(ex)
                                        is_exception = True
                                if self.on_connected:
                                    self.on_connected()
                                self.client_future = asyncio.Future()
                                await self.client_future

                        except Exception as ex:
                            if not is_exception:
                                if self.on_connect_error:
                                    self.on_connect_error(ex)
                                    is_exception = True
                except Exception as ex:
                            if not is_exception:
                                if self.on_connect_error:
                                    self.on_connect_error(ex)
                                    is_exception = True
        except Exception as ex:
            if not is_exception:
                if self.on_connect_error:
                    self.on_connect_error(ex)
                    is_exception = True
        
    async def handle_callback(self) -> tuple[str, str | None]:
        auth_option = self.config.get("auth_option")
        if auth_option:
            params = parse_qs(urlparse(auth_option["callback_url"]).query)
            return params["code"][0], params.get("state", [None])[0]
        raise Exception("'auth_option'未配置'callback_url'")

    async def auth_connect(self, config: MCPStreamableHTTPOption):
        auth_option = config.get("auth_option")
        if not auth_option or not auth_option.get("callback_url"):
            if self.on_connect_error:
                self.on_connect_error(ConnectionError("'auth_option'配置不正确"))
            return
        url_parsed = urlparse(config["url"])
        base_url = f"{url_parsed.scheme}://{url_parsed.netloc}"

        oauth_auth = OAuthClientProvider(
            server_url=base_url,
            client_metadata=OAuthClientMetadata(
                client_name=self.client_info["name"],
                redirect_uris=[AnyUrl(url) for url in auth_option["redirect_uris"]],
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                scope="user"
            ),
            storage=InMemoryTokenStorage(),
            redirect_handler=MCPClient.handle_redirect,
            callback_handler=self.handle_callback
        )

        headers = config.get("headers")
        if headers:
            headers = self.replace_env_key(headers)

        async with httpx.AsyncClient(auth=oauth_auth, follow_redirects=True, headers=headers) as http_client:
            async with streamable_http_client(config["url"], http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await self.session.initialize()
                    self.client_future = asyncio.Future()
                    if self.on_connected:
                        self.on_connected()
                    await self.client_future

    
    async def connect_stdio(self, config: MCPStdioOption):
        try:
            parameters = StdioServerParameters(
                command=config["cmd"],
                args=config["args"],
                env=config.get("env")
            )
            async with stdio_client(parameters) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await self.session.initialize()
                    self.client_future = asyncio.Future()
                    if self.on_connected:
                        self.on_connected()
                    await self.client_future
        except Exception as ex:
            if self.on_connect_error:
                self.on_connect_error(ex)
            logger.error(f"出现异常: {ex}", exc_info=ex)
    
    @staticmethod
    def replace_env_key(headers: dict[str, str], none_policy: Literal["empty", "skip", "remove"] = "empty"):
        new_headers: dict[str, str] = {
            **headers
        }
        for k,v in headers.items():
            search_results = re.findall(r"\$\{([\w\-]+)\}", v)
            if not search_results:
                continue

            temp_v = v
            for key in search_results:
                key_content = os.getenv(key)
                if key_content is None:
                    if none_policy == "empty":
                        temp_v = temp_v.replace(f"${{{key}}}", "")
                    elif none_policy == "remove":
                        new_headers.pop(k, None)
                        break
                    elif none_policy == "skip":
                        continue
                else:
                    temp_v = temp_v.replace(f"${{{key}}}", key_content)
            if k in new_headers:
                new_headers[k] = temp_v
        return new_headers
    
    async def connect(self):
        if "url" in self.config:
            await self.connect_streamable_http(self.config)
        elif "cmd" in self.config:
            await self.connect_stdio(self.config)
        elif self.on_connect_error:
            self.on_connect_error(ConnectionError("mcp配置错误"))
    
    def disconnect(self):
        if self.client_future:
            self.client_future.set_result(None)
    
    def get_session(self):
        if self.session is None:
            raise ConnectionError("MCP未连接")
        return self.session