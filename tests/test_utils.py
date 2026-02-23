import pytest
from unittest.mock import Mock, patch
from src.utils import (
    validate_feed_id,
    format_date,
    format_archived_feeds,
    fetch_datasets,
)


class TestValidateFeedId:
    """Test feed_id validation"""

    def test_valid_feed_id(self):
        """Test that valid feed_id returns True"""
        is_valid, error = validate_feed_id("mdb-503")
        assert is_valid is True
        assert error is None

    def test_valid_feed_id_different_numbers(self):
        """Test various feed_id formats"""
        is_valid, error = validate_feed_id("mdb-1")
        assert is_valid is True
        assert error is None

    def test_none_feed_id(self):
        """Test that None feed_id returns False"""
        is_valid, error = validate_feed_id(None)
        assert is_valid is False
        assert error == "Feed ID is required"

    def test_empty_feed_id(self):
        """Test that empty string feed_id returns False"""
        is_valid, error = validate_feed_id("")
        assert is_valid is False
        assert error == "Feed ID is required"


class TestFormatDate:
    """Test date formatting from ISO to YYYYMMDD"""

    def test_iso_datetime_with_timezone(self):
        """Test ISO datetime with timezone"""
        result = format_date("2025-11-14T17:17:24+00:00")
        assert result == "20251114"

    def test_iso_datetime_z_timezone(self):
        """Test ISO datetime with Z timezone"""
        result = format_date("2025-11-14T17:17:24Z")
        assert result == "20251114"

    def test_simple_date_format(self):
        """Test simple YYYY-MM-DD format"""
        result = format_date("2025-11-14")
        assert result == "20251114"

    def test_different_date(self):
        """Test another date"""
        result = format_date("2024-01-15")
        assert result == "20240115"

    def test_empty_string(self):
        """Test empty string returns empty"""
        result = format_date("")
        assert result == ""

    def test_none_input(self):
        """Test None input returns empty"""
        result = format_date(None)
        assert result == ""

    def test_invalid_format(self):
        """Test invalid date format returns empty"""
        result = format_date("not-a-date")
        assert result == ""

    def test_malformed_iso_datetime(self):
        """Test malformed ISO datetime"""
        result = format_date("2025-13-45T99:99:99Z")
        assert result == ""

    def test_iso_datetime_with_microseconds(self):
        """Test ISO datetime with microseconds"""
        result = format_date("2025-06-30T15:30:45.123456+00:00")
        assert result == "20250630"


class TestFormatArchivedFeeds:
    """Test CSV generation from datasets"""

    def test_empty_datasets(self):
        """Test formatting empty datasets"""
        result = format_archived_feeds([])
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert (
            lines[0]
            == "feed_start_date,feed_end_date,feed_version,archive_url,archive_note"
        )

    def test_header_row(self):
        """Test that header row is correctly formatted"""
        result = format_archived_feeds([])
        assert (
            "feed_start_date,feed_end_date,feed_version,archive_url,archive_note"
            in result
        )

    def test_single_dataset(self):
        """Test formatting a single dataset"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": "Fall 2025",
            }
        ]
        result = format_archived_feeds(datasets)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert "20251107" in result
        assert "20251213" in result
        assert "https://example.com/archive.zip" in result
        assert "Fall 2025" in result

    def test_multiple_datasets_sorted_by_downloaded_at(self):
        """Test that datasets are sorted by downloaded_at in reverse (latest first)"""
        datasets = [
            {
                "service_date_range_start": "2025-01-01",
                "service_date_range_end": "2025-02-01",
                "downloaded_at": "2025-01-10T00:00:00Z",
                "hosted_url": "https://example.com/1.zip",
                "note": "Version 1",
            },
            {
                "service_date_range_start": "2025-03-01",
                "service_date_range_end": "2025-04-01",
                "downloaded_at": "2025-03-10T00:00:00Z",
                "hosted_url": "https://example.com/3.zip",
                "note": "Version 3",
            },
            {
                "service_date_range_start": "2025-02-01",
                "service_date_range_end": "2025-03-01",
                "downloaded_at": "2025-02-10T00:00:00Z",
                "hosted_url": "https://example.com/2.zip",
                "note": "Version 2",
            },
        ]
        result = format_archived_feeds(datasets)
        lines = result.strip().split("\n")

        # Should be 4 lines: header + 3 datasets
        assert len(lines) == 4

        # Latest should be first (2025-03)
        assert "https://example.com/3.zip" in lines[1]
        # Middle should be second (2025-02)
        assert "https://example.com/2.zip" in lines[2]
        # Oldest should be last (2025-01)
        assert "https://example.com/1.zip" in lines[3]

    def test_missing_dates_without_filter(self):
        """Test that rows with missing dates are included when filter_null_dates=False"""
        datasets = [
            {
                "service_date_range_start": None,
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": "Missing start date",
            }
        ]
        result = format_archived_feeds(datasets, filter_null_dates=False)
        lines = result.strip().split("\n")
        # Should have header + 1 data row
        assert len(lines) == 2
        assert "20251213" in result

    def test_missing_dates_with_filter(self):
        """Test that rows with missing dates are excluded when filter_null_dates=True"""
        datasets = [
            {
                "service_date_range_start": None,
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": "Missing start date",
            },
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-15T17:17:24Z",
                "hosted_url": "https://example.com/valid.zip",
                "note": "Valid dates",
            },
        ]
        result = format_archived_feeds(datasets, filter_null_dates=True)
        lines = result.strip().split("\n")
        # Should have header + 1 data row (only the valid one)
        assert len(lines) == 2
        assert "Valid dates" in result
        assert "Missing start date" not in result

    def test_csv_escaping_with_commas(self):
        """Test that CSV values with commas are properly quoted"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": "Note with, comma",
            }
        ]
        result = format_archived_feeds(datasets)
        # CSV writer should quote the note field
        assert '"Note with, comma"' in result

    def test_csv_escaping_with_quotes(self):
        """Test that CSV values with quotes are properly escaped"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": 'Note with "quotes"',
            }
        ]
        result = format_archived_feeds(datasets)
        # CSV writer should escape quotes
        assert '""' in result  # Escaped quote

    def test_missing_optional_fields(self):
        """Test handling of missing optional fields"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
            }
        ]
        result = format_archived_feeds(datasets)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert "20251107" in result

    def test_downloaded_at_used_as_feed_version(self):
        """Test that downloaded_at is used as feed_version"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "downloaded_at": "2025-11-14T17:17:24Z",
                "hosted_url": "https://example.com/archive.zip",
                "note": "Test",
            }
        ]
        result = format_archived_feeds(datasets)
        assert "2025-11-14T17:17:24Z" in result

    def test_dataset_with_missing_downloaded_at(self):
        """Test that missing downloaded_at doesn't break sorting"""
        datasets = [
            {
                "service_date_range_start": "2025-11-07",
                "service_date_range_end": "2025-12-13",
                "hosted_url": "https://example.com/archive.zip",
                "note": "No timestamp",
            }
        ]
        result = format_archived_feeds(datasets)
        lines = result.strip().split("\n")
        assert len(lines) == 2


class TestFetchDatasets:
    """Test fetching datasets from MobilityDatabase API"""

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_with_results_dict(self, mock_auth, mock_get):
        """Test fetching datasets when API returns dict with 'results' key"""
        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "service_date_range_start": "2025-11-07",
                    "service_date_range_end": "2025-12-13",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_datasets("mdb-503")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["service_date_range_start"] == "2025-11-07"

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_with_direct_list(self, mock_auth, mock_get):
        """Test fetching datasets when API returns direct list"""
        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_response = Mock()
        mock_response.json.return_value = [{"service_date_range_start": "2025-11-07"}]
        mock_get.return_value = mock_response

        result = fetch_datasets("mdb-503")

        assert isinstance(result, list)
        assert len(result) == 1

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_empty_results(self, mock_auth, mock_get):
        """Test fetching datasets with empty results"""
        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = fetch_datasets("mdb-503")

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_invalid_response(self, mock_auth, mock_get):
        """Test fetching datasets with invalid response format"""
        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "format"}
        mock_get.return_value = mock_response

        result = fetch_datasets("mdb-503")

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("src.utils.MOBILITY_DB_REFRESH_TOKEN", "fake-refresh-token")
    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_with_valid_token(self, mock_auth, mock_get):
        """Test that auth header is used when token is provided"""
        mock_auth.return_value = {"Authorization": "Bearer valid-token"}
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        fetch_datasets("mdb-503")

        # Check that headers contain the authorization
        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer valid-token"

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_http_error(self, mock_auth, mock_get):
        """Test handling of HTTP errors"""
        import requests

        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_get.side_effect = requests.exceptions.HTTPError("401 Unauthorized")

        with pytest.raises(Exception) as exc_info:
            fetch_datasets("mdb-503")

        assert "Failed to fetch datasets" in str(exc_info.value)

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_timeout(self, mock_auth, mock_get):
        """Test handling of timeout"""
        import requests

        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(Exception) as exc_info:
            fetch_datasets("mdb-503")

        assert "Failed to fetch datasets" in str(exc_info.value)

    @patch("src.utils.requests.get")
    @patch("src.utils.get_mobility_db_auth_header")
    def test_fetch_datasets_url_format(self, mock_auth, mock_get):
        """Test that correct URL is used for the API call"""
        mock_auth.return_value = {"Authorization": "Bearer token"}
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        fetch_datasets("mdb-503")

        # Check that the correct URL was called
        call_args = mock_get.call_args
        url = call_args[0][0]
        assert "gtfs_feeds/mdb-503/datasets" in url
        assert "https://api.mobilitydatabase.org/v1" in url
