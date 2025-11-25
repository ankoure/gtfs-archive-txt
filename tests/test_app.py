from unittest.mock import patch
from src.app import (
    index,
    generate_archived_feeds,
    download_archived_feeds,
    archived_feeds_txt,
    app,
)


class TestIndexEndpoint:
    """Test GET / endpoint"""

    def test_index_returns_dict(self):
        """Test that index endpoint returns dict response"""
        response = index()
        assert isinstance(response, dict)

    def test_index_contains_message(self):
        """Test that index response contains expected message"""
        response = index()
        assert "message" in response
        assert "GTFS" in response["message"]

    def test_index_contains_endpoint_info(self):
        """Test that index response contains endpoint information"""
        response = index()
        assert "endpoint" in response


class TestGenerateArchivedFeedsEndpoint:
    """Test GET /generate endpoint"""

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_returns_dict_with_valid_feed(self, mock_validate, mock_fetch):
        """Test successful generation with valid feed ID"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = generate_archived_feeds()
            assert isinstance(response, dict)
            assert "content" in response

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_includes_csv_content(self, mock_validate, mock_fetch):
        """Test that generate includes CSV content"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = generate_archived_feeds()
            assert "feed_start_date" in response["content"]
            assert "20251107" in response["content"]

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_includes_count(self, mock_validate, mock_fetch):
        """Test that response includes count"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [{"service_date_range_start": "2025-11-07"}]

            response = generate_archived_feeds()
            assert "count" in response
            assert response["count"] == 0  # 1 dataset - 1 header

    @patch("app.app.validate_feed_id")
    def test_generate_returns_400_with_invalid_feed_id(self, mock_validate):
        """Test that invalid feed ID returns 400"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "invalid"}
            mock_validate.return_value = (False, "Invalid feed ID format: invalid")

            response = generate_archived_feeds()
            assert isinstance(response, tuple)
            assert response[1] == 400

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_returns_404_with_empty_results(self, mock_validate, mock_fetch):
        """Test that empty results return 404"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-999"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = []

            response = generate_archived_feeds()
            assert isinstance(response, tuple)
            assert response[1] == 404

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_returns_401_with_auth_error(self, mock_validate, mock_fetch):
        """Test that auth errors return 401"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.side_effect = Exception("Unauthorized: Failed to authenticate")

            response = generate_archived_feeds()
            assert isinstance(response, tuple)
            assert response[1] == 401

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_returns_500_with_generic_error(self, mock_validate, mock_fetch):
        """Test that generic errors return 500"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.side_effect = Exception("Some random error")

            response = generate_archived_feeds()
            assert isinstance(response, tuple)
            assert response[1] == 500

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_includes_feed_id(self, mock_validate, mock_fetch):
        """Test that response includes the feed_id"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [{"service_date_range_start": "2025-01-01"}]

            response = generate_archived_feeds()
            assert response["feed_id"] == "mdb-503"

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_generate_with_filter_null_dates(self, mock_validate, mock_fetch):
        """Test generate with filter_null_dates parameter"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {
                "feed_id": "mdb-503",
                "filter_null_dates": "true",
            }
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-01-01",
                    "service_date_range_end": "2025-02-01",
                    "downloaded_at": "2025-01-10T00:00:00Z",
                    "hosted_url": "https://example.com/1.zip",
                    "note": "Valid",
                }
            ]

            response = generate_archived_feeds()
            assert "content" in response


class TestDownloadArchivedFeedsEndpoint:
    """Test GET /download endpoint"""

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_returns_response_object(self, mock_validate, mock_fetch):
        """Test that download returns Response object"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            from chalice.app import Response

            response = download_archived_feeds()
            assert isinstance(response, Response)

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_returns_200(self, mock_validate, mock_fetch):
        """Test that download returns 200 status"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = download_archived_feeds()
            assert response.status_code == 200

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_content_type_csv(self, mock_validate, mock_fetch):
        """Test that download has CSV content type"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = download_archived_feeds()
            assert response.headers["Content-Type"] == "text/csv"

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_has_attachment_header(self, mock_validate, mock_fetch):
        """Test that download has Content-Disposition header"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = download_archived_feeds()
            assert "Content-Disposition" in response.headers
            assert "attachment" in response.headers["Content-Disposition"]

    @patch("app.app.validate_feed_id")
    def test_download_returns_400_with_invalid_feed_id(self, mock_validate):
        """Test that invalid feed ID returns 400"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "invalid"}
            mock_validate.return_value = (False, "Invalid feed ID")

            response = download_archived_feeds()
            assert response.status_code == 400

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_returns_404_with_empty_results(self, mock_validate, mock_fetch):
        """Test that empty results return 404"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-999"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = []

            response = download_archived_feeds()
            assert response.status_code == 404

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_download_has_cache_control_header(self, mock_validate, mock_fetch):
        """Test that download has Cache-Control header"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = download_archived_feeds()
            assert "Cache-Control" in response.headers
            assert "no-cache" in response.headers["Cache-Control"]


class TestArchivedFeedsTxtEndpoint:
    """Test GET /archived_feeds.txt endpoint"""

    @patch("app.app.download_archived_feeds")
    def test_archived_feeds_txt_calls_download(self, mock_download):
        """Test that archived_feeds.txt calls download_archived_feeds"""
        with patch.object(app, "current_request", create=True) as mock_request:
            from chalice.app import Response

            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_download.return_value = Response(body="csv content", status_code=200)

            archived_feeds_txt()
            mock_download.assert_called_once()


class TestQueryParameters:
    """Test query parameter handling"""

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_feed_id_parameter_extraction(self, mock_validate, mock_fetch):
        """Test that feed_id parameter is extracted"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-custom"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [{"service_date_range_start": "2025-11-07"}]

            generate_archived_feeds()

            # Verify validate_feed_id was called with correct parameter
            mock_validate.assert_called()
            call_args = mock_validate.call_args[0]
            assert call_args[0] == "mdb-custom"

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_filter_null_dates_parameter_true(self, mock_validate, mock_fetch):
        """Test that filter_null_dates=true is recognized"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {
                "feed_id": "mdb-503",
                "filter_null_dates": "true",
            }
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = generate_archived_feeds()
            assert isinstance(response, dict)

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_filter_null_dates_case_insensitive(self, mock_validate, mock_fetch):
        """Test that filter_null_dates is case insensitive"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {
                "feed_id": "mdb-503",
                "filter_null_dates": "TRUE",
            }
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = generate_archived_feeds()
            assert isinstance(response, dict)

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_no_query_params(self, mock_validate, mock_fetch):
        """Test that endpoint works without query params"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = None
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                    "downloaded_at": "2025-11-14T17:17:24Z",
                    "hosted_url": "https://example.com/archive.zip",
                    "note": "Test",
                }
            ]

            response = generate_archived_feeds()
            assert isinstance(response, dict)


class TestErrorHandling:
    """Test error handling"""

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_404_response_includes_feed_id(self, mock_validate, mock_fetch):
        """Test that 404 response includes feed_id"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-999"}
            mock_validate.return_value = (True, None)
            mock_fetch.return_value = []

            response = generate_archived_feeds()
            assert response[0]["feed_id"] == "mdb-999"

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_error_responses_include_error_field(self, mock_validate, mock_fetch):
        """Test that error responses include error field"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "invalid"}
            mock_validate.return_value = (False, "Invalid format")

            response = generate_archived_feeds()
            assert "error" in response[0]

    @patch("app.app.fetch_datasets")
    @patch("app.app.validate_feed_id")
    def test_500_response_structure(self, mock_validate, mock_fetch):
        """Test that 500 response has proper structure"""
        with patch.object(app, "current_request", create=True) as mock_request:
            mock_request.query_params = {"feed_id": "mdb-503"}
            mock_validate.return_value = (True, None)
            mock_fetch.side_effect = Exception("Unexpected error")

            response = generate_archived_feeds()
            assert isinstance(response, tuple)
            assert response[1] == 500
            assert "error" in response[0]
