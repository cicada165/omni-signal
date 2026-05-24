import os
import unittest
from unittest.mock import Mock, patch

from omni_signal.fmp_client import FMPClient, FMPClientError


class TestFMPClient(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict(os.environ, {"FMP_API_KEY": "test-secret"}, clear=True)
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_build_url_redacts_api_key(self) -> None:
        client = FMPClient(base_url="https://financialmodelingprep.com/stable")
        url = client.build_url("/price-target-consensus", {"symbol": "NVDA"})
        self.assertIn("/stable/price-target-consensus?", url)
        self.assertIn("apikey=test-secret", url)
        redacted = client.redact_url(url)
        self.assertNotIn("test-secret", redacted)
        self.assertIn("[redacted]", redacted)

    def test_missing_api_key_raises_clear_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(FMPClientError) as ctx:
                FMPClient()
        self.assertIn("Missing FMP_API_KEY", str(ctx.exception))

    @patch("omni_signal.fmp_client.urlopen")
    def test_http_call_uses_encoded_url_and_does_not_log_key(self, mock_urlopen) -> None:
        response = Mock()
        response.read.return_value = b'{"ok": true}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = response

        client = FMPClient()
        payload = client.get_price_target_consensus("NVDA")

        self.assertEqual(payload, {"ok": True})
        called_request = mock_urlopen.call_args.args[0]
        self.assertIn("apikey=test-secret", called_request.full_url)
        self.assertNotIn("test-secret", client.redact_url(called_request.full_url))
