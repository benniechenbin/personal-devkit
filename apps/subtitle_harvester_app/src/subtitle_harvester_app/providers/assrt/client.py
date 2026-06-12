from __future__ import annotations

from typing import Any, cast

import httpx


class AssrtQuotaExceeded(RuntimeError):
    pass


class AssrtApiClient:
    """Assrt API 客户端。

    只封装 HTTP API，不做字幕业务筛选，不做下载，不做解包。
    """

    BASE_URL = "https://api.assrt.net"

    def __init__(
        self,
        *,
        token: str,
        timeout: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.token = token
        self.client = client or httpx.Client(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    def close(self) -> None:
        self.client.close()

    def search(
        self,
        query: str,
        *,
        count: int = 10,
        position: int = 0,
        filelist: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "q": query,
            "cnt": count,
            "pos": position,
        }
        if filelist:
            params["filelist"] = 1

        return self._get("/v1/sub/search", params=params)

    def detail(self, subtitle_id: int) -> dict[str, Any]:
        return self._get("/v1/sub/detail", params={"id": subtitle_id})

    def quota(self) -> dict[str, Any]:
        return self._get("/v1/user/quota")

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_params = dict(params or {})

        try:
            response = self.client.get(
                path,
                params=request_params,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.token}",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 509:
                raise AssrtQuotaExceeded("Assrt API quota exceeded or rate limited.") from exc
            raise

        payload = cast(dict[str, Any], response.json())
        status = payload.get("status")
        if status not in (0, "0", None):
            raise RuntimeError(f"Assrt API 返回错误：status={status}, payload={payload}")

        return payload
