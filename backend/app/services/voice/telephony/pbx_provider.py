from __future__ import annotations

import httpx


class AsteriskPbxProvider:
    """Asterisk ARI adapter; never reports a call without a real ARI response."""

    def __init__(self, base_url: str, username: str, password: str, endpoint: str = "/ari/channels") -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.endpoint = endpoint

    async def create_call(self, to: str, caller_id: str, app: str) -> str:
        if not self.base_url or not self.username or not self.password:
            raise ValueError("ASTERISK_NOT_CONFIGURED")
        if not to.strip() or not caller_id.strip() or not app.strip():
            raise ValueError("ASTERISK_CALL_FIELDS_REQUIRED")
        async with httpx.AsyncClient(timeout=30, auth=(self.username, self.password)) as client:
            response = await client.post(
                f"{self.base_url}{self.endpoint}",
                params={"endpoint": to, "app": app, "callerId": caller_id},
            )
        if response.is_error:
            raise ValueError(f"ASTERISK_CALL_FAILED: HTTP_{response.status_code}")
        data = response.json()
        call_id = data.get("id")
        if not call_id:
            raise ValueError("ASTERISK_CALL_FAILED: CALL_ID_MISSING")
        return str(call_id)

    async def get_call_status(self, call_id: str) -> str:
        if not call_id:
            raise ValueError("ASTERISK_CALL_ID_REQUIRED")
        async with httpx.AsyncClient(timeout=15, auth=(self.username, self.password)) as client:
            response = await client.get(f"{self.base_url}{self.endpoint}/{call_id}")
        if response.is_error:
            raise ValueError(f"ASTERISK_STATUS_FAILED: HTTP_{response.status_code}")
        return str(response.json().get("state", "UNKNOWN")).upper()

    async def health_check(self) -> bool:
        if not self.base_url or not self.username or not self.password:
            return False
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.username, self.password)) as client:
                response = await client.get(f"{self.base_url}/ari/asterisk/info")
            return response.is_success
        except httpx.HTTPError:
            return False
