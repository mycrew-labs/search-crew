"""统一 HTTP 客户端（stdlib urllib，零依赖）。

所有 backend / 站点适配器调用 HTTP 必须经此模块，便于：
- 统一超时、错误分类
- 在出口统一调用 usage.record()（cost 打点）
- 集中拦截 retryable / non-retryable 错误
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from . import BackendError

DEFAULT_TIMEOUT = 30
USER_AGENT = "search-crew/0.1 (+https://github.com/mycrew-labs/search-crew)"


def _record_call(*, backend: str, endpoint: str, status: int | str, latency_ms: int, units: int | None) -> None:
    """打点钩子。延迟 import 避免循环依赖。失败不阻塞业务。"""
    try:
        from . import usage  # noqa: PLC0415  延迟导入

        usage.record(
            backend=backend,
            endpoint=endpoint,
            status=status,
            latency_ms=latency_ms,
            tokens_or_units=units,
        )
    except Exception as e:  # 打点不应阻塞业务
        import sys

        print(f"[_http] usage.record failed: {e}", file=sys.stderr)


def request_json(
    method: str,
    url: str,
    *,
    backend: str,
    endpoint: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    timeout: int = DEFAULT_TIMEOUT,
    units: int | None = 1,
) -> Any:
    """发起 JSON 请求并返回反序列化结果。

    `backend` / `endpoint` 用于打点；`units` 用于 cost 估算（默认 1 次请求 = 1 unit）。
    """
    if params:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{urllib.parse.urlencode(params, doseq=True)}"

    data = None
    final_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        final_headers["Content-Type"] = "application/json"
    if headers:
        final_headers.update(headers)

    req = urllib.request.Request(url, data=data, method=method, headers=final_headers)
    start = time.monotonic()
    status: int | str = "error"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        retryable = e.code in (429, 502, 503, 504)
        raise BackendError(backend, f"HTTP {e.code}: {body or e.reason}", retryable=retryable) from e
    except urllib.error.URLError as e:
        status = "network-error"
        raise BackendError(backend, f"网络错误: {e.reason}", retryable=True) from e
    except TimeoutError as e:
        status = "timeout"
        raise BackendError(backend, "请求超时", retryable=True) from e
    finally:
        _record_call(
            backend=backend,
            endpoint=endpoint,
            status=status,
            latency_ms=int((time.monotonic() - start) * 1000),
            units=units,
        )

    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise BackendError(backend, f"非 JSON 响应: {raw[:200]}") from e


def request_text(
    method: str,
    url: str,
    *,
    backend: str,
    endpoint: str,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    units: int | None = 1,
) -> str:
    """发起请求返回原文（用于抓取页面 / markdown）。"""
    final_headers = {"User-Agent": USER_AGENT}
    if headers:
        final_headers.update(headers)
    req = urllib.request.Request(url, method=method, headers=final_headers)
    start = time.monotonic()
    status: int | str = "error"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raise BackendError(backend, f"HTTP {e.code}: {e.reason}", retryable=e.code in (429, 502, 503, 504)) from e
    except urllib.error.URLError as e:
        status = "network-error"
        raise BackendError(backend, f"网络错误: {e.reason}", retryable=True) from e
    finally:
        _record_call(
            backend=backend,
            endpoint=endpoint,
            status=status,
            latency_ms=int((time.monotonic() - start) * 1000),
            units=units,
        )
