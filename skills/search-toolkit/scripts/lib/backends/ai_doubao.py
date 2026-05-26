"""豆包 / 火山方舟（Volcengine Ark）联网搜索 backend（Responses API + web_search 内置工具）。

API key 从火山方舟控制台获取，但本 backend 对外叫「doubao」（品牌名）。方舟实际托管多家
模型（Doubao / DeepSeek / Kimi / Qwen 等），由 routing.yaml ai_summary.models.doubao 指定用哪个。

文档：
- 常规在线推理 / Responses API: https://www.volcengine.com/docs/82379/2121998
- Web Search 联网内容插件: https://www.volcengine.com/docs/82379/1756990

最后验证：2026-05-23

注意：联网搜索走 Responses API（/api/v3/responses）+ 内置 `web_search` tool，
不是 chat/completions。model 必须填**API model ID**（带日期的小写格式，
如 `doubao-seed-2-0-pro-260215` 或 `deepseek-v4-flash-260425`），不是 console 显示名
（如「Doubao-Seed-2.0-pro」）。模型需先在方舟控制台「开通管理」里开通；列出账号可用 model：
  GET https://ark.cn-beijing.volces.com/api/v3/models
响应结构与 xAI Responses API 一致，复用 ai_common.parse_responses_api。

model 不在代码 hardcode：由调用方（search.py）从 routing.yaml ai_summary.models.doubao
按 subagent 分层（fast/deep）解析后传入。
"""

from __future__ import annotations

from typing import Any

from .. import BackendError, env
from .. import _http
from .ai_common import make_envelope, parse_responses_api

ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/responses"
BACKEND = "doubao"
API_KEY_ENV = "DOUBAO_API_KEY"


def is_available() -> bool:
    return env(API_KEY_ENV) is not None


def search(query: str, *, max_results: int = 10, model: str | None = None) -> dict[str, Any]:
    api_key = env(API_KEY_ENV)
    if not api_key:
        raise BackendError(BACKEND, f"缺少 {API_KEY_ENV}")
    if not model:
        raise BackendError(BACKEND, "未配置 model，请在 routing.yaml ai_summary.models.doubao 设置 fast/deep")

    body = {
        "model": model,
        "input": [{"role": "user", "content": query}],
        "tools": [{"type": "web_search"}],
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    data = _http.request_json(
        "POST",
        ENDPOINT,
        backend=BACKEND,
        endpoint="responses",
        headers=headers,
        json_body=body,
        timeout=90,
        query=query,
    )

    try:
        summary, citations = parse_responses_api(data, BACKEND)
    except BackendError:
        raise
    except Exception as e:
        raise BackendError(BACKEND, f"doubao 响应解析失败: {e}") from e

    return make_envelope(backend=BACKEND, summary=summary, citations=citations[:max_results] if max_results else citations)
