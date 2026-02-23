import re
import requests
from datetime import datetime
from io import StringIO
import csv
from urllib.parse import quote
from auth import get_mobility_db_auth_header
from constants import MOBILITY_DB_API, MOBILITY_DB_REFRESH_TOKEN


def validate_feed_id(feed_id):
    """Validate feed_id format (must match mdb-{number} pattern)"""
    if not feed_id:
        return False, "Feed ID is required"

    if not re.match(r"^mdb-\d+$", feed_id):
        return False, f"Invalid feed ID format: {feed_id}. Expected format: mdb-123"

    return True, None


def fetch_datasets(feed_id):
    """Fetch all datasets for a given feed from MobilityDatabase"""
    try:
        url = f"{MOBILITY_DB_API}/gtfs_feeds/{quote(feed_id, safe='')}/datasets"
        headers = {"Accept": "application/json", "User-Agent": "archived-feeds-api/1.0"}

        # Add authorization using refresh token
        if MOBILITY_DB_REFRESH_TOKEN:
            auth_header = get_mobility_db_auth_header(MOBILITY_DB_REFRESH_TOKEN)
            headers.update(auth_header)

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        datasets = response.json()

        if isinstance(datasets, dict) and "results" in datasets:
            return datasets["results"]
        elif isinstance(datasets, list):
            return datasets
        else:
            return []

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise Exception(
                "Unauthorized: Failed to authenticate with MobilityDatabase. Check MOBILITY_DB_REFRESH_TOKEN environment variable."
            )
        raise Exception(f"Failed to fetch datasets from MobilityDatabase: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch datasets from MobilityDatabase: {str(e)}")


def format_archived_feeds(datasets, filter_null_dates=False):
    """Format datasets as CSV in archived_feeds.txt format

    Args:
        datasets: List of dataset dictionaries from MobilityDatabase
        filter_null_dates: If True, exclude rows with missing feed_start_date or feed_end_date
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "feed_start_date",
            "feed_end_date",
            "feed_version",
            "archive_url",
            "archive_note",
        ]
    )

    # Sort datasets by latest first
    sorted_datasets = sorted(
        datasets, key=lambda x: x.get("downloaded_at", ""), reverse=True
    )

    for dataset in sorted_datasets:
        # Map Mobility Database API fields to archived_feeds.txt format
        feed_start_date = format_date(dataset.get("service_date_range_start"))
        feed_end_date = format_date(dataset.get("service_date_range_end"))

        # Skip this row if filtering is enabled and either date is missing
        if filter_null_dates and (not feed_start_date or not feed_end_date):
            continue

        # Use downloaded_at timestamp as feed_version
        downloaded_at = dataset.get("downloaded_at", "")
        feed_version = downloaded_at

        # Get the hosted URL from Mobility Database
        archive_url = dataset.get("hosted_url", "")

        # Get notes (singular in API)
        archive_note = dataset.get("note", "") or ""

        writer.writerow(
            [feed_start_date, feed_end_date, feed_version, archive_url, archive_note]
        )

    return output.getvalue()


def format_date(date_string):
    """Convert ISO date string to YYYYMMDD format"""
    if not date_string:
        return ""

    try:
        # Handle ISO format dates
        if "T" in date_string:
            date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        else:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")

        return date_obj.strftime("%Y%m%d")
    except (ValueError, AttributeError):
        return ""
