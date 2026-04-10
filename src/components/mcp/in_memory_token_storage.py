from mcp.shared.auth import (
    OAuthClientInformationFull,
    OAuthToken
)
from mcp.client.auth import (
    TokenStorage
)

class InMemoryTokenStorage(TokenStorage):
    def __init__(self):
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None
    
    async def get_tokens(self) -> OAuthToken | None:
        return self.tokens
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens
    
    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self.client_info
    
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_info = client_info
    
