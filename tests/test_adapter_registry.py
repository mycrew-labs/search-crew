"""TC-AGENT-003：站点适配器注册表（仅注册关系，不实跑 HTTP）。"""

from __future__ import annotations

import os
import pathlib
import tempfile
import textwrap
import unittest

from lib.sites import get_adapter, list_adapters


class TestAdapterRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name
        (pathlib.Path(self.tmp.name) / "search-crew" / "adapters").mkdir(parents=True)

    def tearDown(self) -> None:
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.tmp.cleanup()

    def test_builtin_hosts(self) -> None:
        adapters = list_adapters()
        self.assertIn("github.com", adapters["builtin"])
        self.assertIn("developer.mozilla.org", adapters["builtin"])
        self.assertIn("npmjs.com", adapters["builtin"])

    def test_get_builtin_adapter(self) -> None:
        fn = get_adapter("github.com")
        self.assertIsNotNone(fn)
        # 大小写 / 带协议都能解析
        self.assertIsNotNone(get_adapter("https://GitHub.com/some/path"))

    def test_get_algolia_adapter(self) -> None:
        fn = get_adapter("react.dev")
        self.assertIsNotNone(fn)

    def test_user_python_adapter_loaded(self) -> None:
        adapter_path = pathlib.Path(self.tmp.name) / "search-crew" / "adapters" / "custom_site.py"
        adapter_path.write_text(
            textwrap.dedent(
                """\
                SITE = "fake.example"

                def search(query, max_results=10, **_):
                    return [{"title": "stub", "url": "https://fake.example", "snippet": "ok", "extra": {}}]
                """
            ),
            encoding="utf-8",
        )
        adapters = list_adapters()
        self.assertIn("fake.example", adapters["user_python"])
        fn = get_adapter("fake.example")
        self.assertIsNotNone(fn)
        results = fn("test")
        self.assertEqual(results[0]["title"], "stub")

    def test_user_yaml_adapter_registered(self) -> None:
        yaml_path = pathlib.Path(self.tmp.name) / "search-crew" / "adapters" / "yaml_site.yaml"
        yaml_path.write_text(
            textwrap.dedent(
                """\
                site: yamlsite.example
                search_url: "https://yamlsite.example/search?q={query}"
                result_selector:
                  list: ".result"
                  title: "h3 a"
                  url: "h3 a@href"
                  snippet: ".excerpt"
                """
            ),
            encoding="utf-8",
        )
        adapters = list_adapters()
        self.assertIn("yamlsite.example", adapters["user_yaml"])
        # 不实跑 HTTP；只验证注册成功
        fn = get_adapter("yamlsite.example")
        self.assertIsNotNone(fn)

    def test_unknown_host_returns_none(self) -> None:
        self.assertIsNone(get_adapter("nowhere.local"))


if __name__ == "__main__":
    unittest.main()
