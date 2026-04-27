"""Pooled HTTP client for same-host REST (IBM BPM exposed API, FileNet / ICN middleware, etc.)."""

from __future__ import annotations

import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def _build_session(pool_connections: int, pool_maxsize: int) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.4,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
    )
    adapter = HTTPAdapter(
        pool_connections=max(1, pool_connections),
        pool_maxsize=max(1, pool_maxsize),
        max_retries=retries,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class EnterpriseRestConnector:
    """
    Keeps a requests.Session with urllib3 connection pooling for repeated GETs
    against one BPM or FileNet (or proxy) base URL.
    """

    def __init__(
        self,
        label: str,
        base_url: str,
        pool_connections: int = 10,
        pool_maxsize: int = 32,
        timeout_sec: float = 120.0,
        username: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ) -> None:
        self.label = label
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.pool_connections = int(pool_connections)
        self.pool_maxsize = int(pool_maxsize)
        self._session = _build_session(pool_connections, pool_maxsize)
        parsed = urlparse(self.base_url)
        self._allowed_netloc = (parsed.netloc or "").lower()

        tok = (bearer_token or "").strip()
        if tok:
            self._session.headers["Authorization"] = f"Bearer {tok}"
        else:
            u = (username or "").strip()
            p = (password or "").strip()
            if u:
                self._session.auth = HTTPBasicAuth(u, p)

    def describe(self) -> dict:
        return {
            "label": self.label,
            "base_url": self.base_url,
            "pool_connections": self.pool_connections,
            "pool_maxsize": self.pool_maxsize,
            "timeout_sec": self.timeout_sec,
        }

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass

    def _assert_same_host(self, url: str) -> None:
        netloc = (urlparse(url).netloc or "").lower()
        if not netloc or netloc != self._allowed_netloc:
            raise ValueError(
                f"{self.label}: URL must use the same host and port as the configured base ({self._allowed_netloc!r})"
            )

    def get_bytes(
        self,
        *,
        relative_path: Optional[str] = None,
        resource_url: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        if resource_url and relative_path:
            raise ValueError("Provide only one of resource_url or relative_path")
        if resource_url:
            url = resource_url.strip()
            self._assert_same_host(url)
        elif relative_path:
            rel = relative_path.strip().lstrip("/")
            if not rel:
                raise ValueError("relative_path is empty")
            url = f"{self.base_url.rstrip('/')}/{rel}"
            self._assert_same_host(url)
        else:
            raise ValueError("relative_path or resource_url is required")

        logger.info("%s GET %s", self.label, url)
        resp: Response = self._session.get(url, timeout=self.timeout_sec)
        resp.raise_for_status()
        return resp.content, (resp.headers.get("Content-Type") or "application/octet-stream").split(";")[0].strip()
