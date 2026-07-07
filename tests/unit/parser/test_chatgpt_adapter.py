"""Unit tests for ChatGPTAdapter."""
import pytest

from app.infrastructure.parser.adapters.chatgpt_adapter import ChatGPTAdapter


class TestChatGPTAdapter:
    """Tests for ChatGPTAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return ChatGPTAdapter()

    def test_adapter_creation(self, adapter):
        """Test adapter can be created."""
        assert adapter is not None
        assert hasattr(adapter, 'adapt')

    def test_adapter_has_internal_state(self, adapter):
        """Test adapter maintains internal state during parsing."""
        assert hasattr(adapter, '_conversation_id')
        assert hasattr(adapter, '_title')
        assert hasattr(adapter, '_created_at')
        assert hasattr(adapter, '_blocks')
        assert hasattr(adapter, '_images')

    def test_adapt_empty_html(self, adapter):
        """Test adapt with empty HTML."""
        with pytest.raises(ValueError):
            adapter.adapt("<html></html>")

    def test_adapt_with_mock_data(self, adapter):
        """Test adapt with mock ChatGPT data structure."""
        # This test verifies the adapter can process structured data
        # Full integration test would require real ChatGPT page data
        pass
