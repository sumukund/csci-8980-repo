# token_manager.py
import os
import time
import threading
import base64
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()


class TokenError(RuntimeError):
    """Raised when we can’t obtain or refresh the bearer token."""


class TokenManager:
    """
    Thread-safe helper that fetches and refreshes a bearer token from the
    corporate OAuth (NUA) server.

    Call `get_token()` whenever you need a valid token; the class refreshes it
    ~5 minutes before expiry.
    """

    def __init__(
        self,
        auth_url: str,
        username: str,
        password: str,
        client_id: str,
        client_secret: str,
        token_env_var: str = "API_TOKEN",
        token_validity_buffer: int = 300,
    ):
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_env_var = token_env_var
        self.token_validity_buffer = token_validity_buffer

        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_expiry: float = 0

    def get_token(self) -> str:
        """Return a valid bearer token, refreshing if it’s near expiry."""
        with self._lock:
            now = time.time()
            if (
                self._token is None
                or now >= self._token_expiry - self.token_validity_buffer
            ):
                self._refresh()
            if self._token is None:
                raise TokenError("Failed to obtain a valid token")
            return self._token

    def _refresh(self) -> None:
        """Fetch a new token from the OAuth endpoint."""
        params = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "scope": "profile email openid",
        }

        basic = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic}",
        }

        try:
            resp = requests.post(
                self.auth_url,
                headers=headers,
                data=urllib.parse.urlencode(params),
                verify="certs/tgt-ca-bundle.crt",
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()

            token = payload.get("access_token")
            if not token:
                raise TokenError("Authentication failed: no access token returned")

            self._token = token
            self._token_expiry = time.time() + payload.get("expires_in", 18_000)

            os.environ[self.token_env_var] = token

        except requests.RequestException as exc:
            raise TokenError(f"Authentication failed: {exc}") from exc

def _build_default_manager() -> TokenManager:
    """Create a TokenManager from environment variables / .env."""
    auth_url = os.getenv("AUTH_URL")
    username = os.getenv("NUA_USER")
    password = os.getenv("NUA_PASS")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not all([auth_url, username, password, client_id, client_secret]):
        raise ValueError(
            "Missing one or more of AUTH_URL, NUA_USER, NUA_PASS, "
            "CLIENT_ID, CLIENT_SECRET in environment or .env file."
        )

    assert auth_url is not None
    assert username is not None
    assert password is not None
    assert client_id is not None
    assert client_secret is not None

    return TokenManager(
        auth_url=auth_url,
        username=username,
        password=password,
        client_id=client_id,
        client_secret=client_secret,
    )


_token_manager = _build_default_manager()


def get_token() -> str:
    """Module-level helper for one-liners."""
    return _token_manager.get_token()