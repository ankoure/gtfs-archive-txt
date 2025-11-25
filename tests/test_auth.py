import pytest
import time
from unittest.mock import Mock, patch
from src.auth import (
    refresh_access_token,
    get_valid_access_token,
    get_mobility_db_auth_header,
    _token_cache,
)


class TestRefreshAccessToken:
    """Test access token refresh functionality"""

    def setup_method(self):
        """Clear token cache before each test"""
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = None

    @patch("app.auth.requests.post")
    def test_refresh_access_token_success(self, mock_post):
        """Test successful token refresh"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600, 
        }
        mock_post.return_value = mock_response

        token = refresh_access_token("valid-refresh-token")

        assert token == "new-access-token"
        assert _token_cache["access_token"] == "new-access-token"
        assert _token_cache["expires_at"] is not None

    @patch("app.auth.requests.post")
    def test_refresh_access_token_with_custom_expiry(self, mock_post):
        """Test token refresh with custom expiry time"""
        current_time = time.time()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "expires_in": 7200,
        }
        mock_post.return_value = mock_response

        token = refresh_access_token("refresh-token")

        assert token == "token123"
        # Should refresh 60 seconds before expiry: current_time + 7200 - 60
        expected_expiry = current_time + 7200 - 60
        assert abs(_token_cache["expires_at"] - expected_expiry) < 2

    @patch("app.auth.requests.post")
    def test_refresh_access_token_default_expiry(self, mock_post):
        """Test that default expiry is 1 hour when not provided"""
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token123"}
        mock_post.return_value = mock_response

        token = refresh_access_token("refresh-token")

        assert token == "token123"
        assert _token_cache["expires_at"] is not None

    @patch("app.auth.requests.post")
    def test_refresh_access_token_invalid_refresh_token_empty(self, mock_post):
        """Test error with empty refresh token"""
        with pytest.raises(Exception) as exc_info:
            refresh_access_token("")

        assert "Invalid refresh token format" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_invalid_refresh_token_none(self, mock_post):
        """Test error with None refresh token"""
        with pytest.raises(Exception) as exc_info:
            refresh_access_token(None)

        assert "Invalid refresh token format" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_invalid_refresh_token_short(self, mock_post):
        """Test error with too-short refresh token"""
        with pytest.raises(Exception) as exc_info:
            refresh_access_token("short")

        assert "Invalid refresh token format" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_no_access_token_in_response(self, mock_post):
        """Test error when response has no access_token"""
        mock_response = Mock()
        mock_response.json.return_value = {"expires_in": 3600}
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            refresh_access_token("valid-refresh-token")

        assert "No access token in response" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_network_error(self, mock_post):
        """Test handling of network errors"""
        mock_post.side_effect = Exception("Network timeout")

        with pytest.raises(Exception) as exc_info:
            refresh_access_token("valid-refresh-token")

        assert "Error refreshing token" in str(
            exc_info.value
        ) or "Failed to refresh access token" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_request_exception(self, mock_post):
        """Test handling of request exceptions"""
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(Exception) as exc_info:
            refresh_access_token("valid-refresh-token")

        assert "Failed to refresh access token" in str(exc_info.value)

    @patch("app.auth.requests.post")
    def test_refresh_access_token_correct_endpoint(self, mock_post):
        """Test that correct token endpoint is used"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "api.mobilitydatabase.org" in url
        assert "/tokens" in url

    @patch("app.auth.requests.post")
    def test_refresh_access_token_request_format(self, mock_post):
        """Test that refresh token is sent in correct format"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("my-refresh-token")

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["refresh_token"] == "my-refresh-token"

    @patch("app.auth.requests.post")
    def test_refresh_access_token_timeout_setting(self, mock_post):
        """Test that timeout is set for the request"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        call_kwargs = mock_post.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 10


class TestGetValidAccessToken:
    """Test getting a valid access token with caching"""

    def setup_method(self):
        """Clear token cache before each test"""
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = None

    @patch("app.auth.refresh_access_token")
    def test_get_valid_access_token_no_cache(self, mock_refresh):
        """Test getting token when cache is empty"""
        mock_refresh.return_value = "new-token"
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = None

        token = get_valid_access_token("refresh-token")

        assert token == "new-token"
        mock_refresh.assert_called_once_with("refresh-token")

    @patch("app.auth.refresh_access_token")
    def test_get_valid_access_token_cache_not_expired(self, mock_refresh):
        """Test that cached token is returned if not expired"""
        _token_cache["access_token"] = "cached-token"
        _token_cache["expires_at"] = time.time() + 3600  # Expires in 1 hour

        token = get_valid_access_token("refresh-token")

        assert token == "cached-token"
        # refresh_access_token should not be called
        mock_refresh.assert_not_called()

    @patch("app.auth.refresh_access_token")
    def test_get_valid_access_token_cache_expired(self, mock_refresh):
        """Test that new token is fetched when cache is expired"""
        _token_cache["access_token"] = "old-token"
        _token_cache["expires_at"] = time.time() - 100  # Expired 100 seconds ago
        mock_refresh.return_value = "new-token"

        token = get_valid_access_token("refresh-token")

        assert token == "new-token"
        mock_refresh.assert_called_once_with("refresh-token")

    @patch("app.auth.refresh_access_token")
    def test_get_valid_access_token_no_expiry_time(self, mock_refresh):
        """Test that new token is fetched when expiry time is None"""
        _token_cache["access_token"] = "some-token"
        _token_cache["expires_at"] = None
        mock_refresh.return_value = "new-token"

        token = get_valid_access_token("refresh-token")

        assert token == "new-token"
        mock_refresh.assert_called_once_with("refresh-token")

    @patch("app.auth.refresh_access_token")
    def test_get_valid_access_token_no_cached_token(self, mock_refresh):
        """Test that new token is fetched when cached token is None"""
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = time.time() + 3600
        mock_refresh.return_value = "new-token"

        token = get_valid_access_token("refresh-token")

        assert token == "new-token"
        mock_refresh.assert_called_once_with("refresh-token")


class TestGetMobilityDbAuthHeader:
    """Test getting authorization header"""

    def setup_method(self):
        """Clear token cache before each test"""
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = None

    @patch("app.auth.get_valid_access_token")
    def test_get_mobility_db_auth_header_format(self, mock_get_token):
        """Test that auth header is in correct format"""
        mock_get_token.return_value = "test-access-token"

        header = get_mobility_db_auth_header("refresh-token")

        assert "Authorization" in header
        assert header["Authorization"] == "Bearer test-access-token"

    @patch("app.auth.get_valid_access_token")
    def test_get_mobility_db_auth_header_calls_get_valid_token(self, mock_get_token):
        """Test that get_valid_access_token is called"""
        mock_get_token.return_value = "token"

        get_mobility_db_auth_header("my-refresh-token")

        mock_get_token.assert_called_once_with("my-refresh-token")

    @patch("app.auth.get_valid_access_token")
    def test_get_mobility_db_auth_header_different_tokens(self, mock_get_token):
        """Test with different token values"""
        mock_get_token.return_value = "long-token-value-12345"

        header = get_mobility_db_auth_header("refresh-token")

        assert header["Authorization"] == "Bearer long-token-value-12345"

    @patch("app.auth.get_valid_access_token")
    def test_get_mobility_db_auth_header_error_propagation(self, mock_get_token):
        """Test that exceptions are propagated"""
        mock_get_token.side_effect = Exception("Token refresh failed")

        with pytest.raises(Exception) as exc_info:
            get_mobility_db_auth_header("refresh-token")

        assert "Token refresh failed" in str(exc_info.value)


class TestTokenCache:
    """Test token caching behavior"""

    def setup_method(self):
        """Clear token cache before each test"""
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = None

    @patch("app.auth.requests.post")
    def test_token_cache_stores_token(self, mock_post):
        """Test that token is stored in cache"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "cached-token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        assert _token_cache["access_token"] == "cached-token"

    @patch("app.auth.requests.post")
    def test_token_cache_stores_expiry(self, mock_post):
        """Test that expiry time is stored in cache"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        assert _token_cache["expires_at"] is not None
        assert isinstance(_token_cache["expires_at"], float)

    @patch("app.auth.requests.post")
    def test_token_cache_resets_on_new_token(self, mock_post):
        """Test that cache is properly updated on new token"""
        _token_cache["access_token"] = "old-token"
        _token_cache["expires_at"] = time.time() + 100

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        assert _token_cache["access_token"] == "new-token"

    @patch("app.auth.requests.post")
    def test_token_refresh_happens_60_seconds_before_expiry(self, mock_post):
        """Test that token refresh threshold is 60 seconds"""
        current_time = time.time()
        mock_response = Mock()
        expires_in = 300  # 5 minutes
        mock_response.json.return_value = {
            "access_token": "token",
            "expires_in": expires_in,
        }
        mock_post.return_value = mock_response

        refresh_access_token("refresh-token")

        # Expiry should be current_time + expires_in - 60
        expected_expiry = current_time + expires_in - 60
        actual_expiry = _token_cache["expires_at"]

        # Allow 2 second tolerance for test execution time
        assert abs(actual_expiry - expected_expiry) < 2
