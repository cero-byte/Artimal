import ssl
import sys
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
sys.path.insert(0, str(WEB_ROOT))

import server  # noqa: E402


class ServerHelperTests(unittest.TestCase):
    def test_extract_json_accepts_fenced_content(self):
        value = server.extract_json('```json\n{"ok": true}\n```')
        self.assertEqual(value, {"ok": True})

    def test_extract_json_rejects_non_json(self):
        self.assertIsNone(server.extract_json("not json"))

    def test_participant_id_is_path_safe(self):
        handler = object.__new__(server.ArtimalHandler)
        self.assertEqual(handler._safe_pid("../P 001/测试"), "_P_001_测试")

    def test_tls_verification_is_enabled(self):
        context = server.get_ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_request_errors_keep_their_http_status(self):
        handler = object.__new__(server.ArtimalHandler)
        self.assertEqual(
            handler._api_error(server.RequestError(413, "too large")),
            (413, "too large"),
        )

    def test_current_image_models_are_allowlisted(self):
        self.assertEqual(
            server.ALLOWED_IMAGE_MODELS,
            {"gpt-image-1-mini", "gpt-image-2"},
        )

    def test_config_file_supplies_api_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                '{"openai":{"api_base_url":"https://example.test/v1/","api_key":"secret"}}',
                encoding="utf-8",
            )
            config = server.load_config(config_path)
        self.assertEqual(config["openai"]["api_base_url"], "https://example.test/v1")
        self.assertEqual(config["openai"]["api_key"], "secret")

    def test_openai_url_uses_configured_base(self):
        original = server.APP_CONFIG
        try:
            server.APP_CONFIG = {
                "openai": {"api_base_url": "https://example.test/v1", "api_key": ""}
            }
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(
                    server.openai_api_url("chat/completions"),
                    "https://example.test/v1/chat/completions",
                )
        finally:
            server.APP_CONFIG = original

    def test_environment_key_overrides_config_key(self):
        original = server.APP_CONFIG
        try:
            server.APP_CONFIG = {
                "openai": {"api_base_url": "https://example.test/v1", "api_key": "file-key"}
            }
            with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}, clear=True):
                self.assertEqual(server.configured_api_key(), "env-key")
        finally:
            server.APP_CONFIG = original

    def test_html_model_references_are_documented(self):
        attribution_text = (
            WEB_ROOT.parent / "ATTRIBUTIONS.md"
        ).read_text(encoding="utf-8")
        for language in ("en", "zh"):
            page = (WEB_ROOT / language / "index.html").read_text(encoding="utf-8")
            references = set(re.findall(r"\.\./assets/([a-z]+\.glb)", page))
            self.assertGreaterEqual(len(references), 5)
            for filename in references:
                self.assertIn(f"`{filename}`", attribution_text)


if __name__ == "__main__":
    unittest.main()
