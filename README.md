# GTFS Archive Feeds API

A Chalice-based AWS Lambda application that generates `archived_feeds.txt` files from MobilityDatabase GTFS feed history.

## Overview

This application provides HTTP endpoints to fetch historical GTFS feed data from MobilityDatabase and format it as a CSV file compatible with the MBTA's `archived_feeds.txt` format.

## Features

- **Automatic feed history retrieval** from MobilityDatabase API
- **Support for any Mobility Database feed** via query parameter
- **CSV generation** in MBTA archived_feeds.txt format
- **Date formatting** (converts ISO dates to YYYYMMDD)
- **Feed ID validation** to ensure correct format
- **Error handling** with informative error messages

## Setup

### Prerequisites

- Python 3.12+
- AWS credentials configured (for deployment)
- MobilityDatabase API key (get from <https://mobilitydatabase.org/sign-in>)

### Installation

1. Install dependencies:

```bash
uv sync
```

2. Set up environment variable with your MobilityDatabase API key:

```bash
export MOBILITY_DB_REFRESH_TOKEN="your-access-token-here"
```

Or create a .env file with MOBILITY_DB_REFRESH_TOKEN="your-access-token-here"

## Getting an API Key

1. Sign up at <https://mobilitydatabase.org>
2. Go to Account Settings
3. Find your "Refresh Token" or "Access Token"
4. Use this token as your `MOBILITY_DB_REFRESH_TOKEN`

## Local Development

Run the local development server:

```bash
chalice local
```

For access over local network:

```bash
chalice local --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

### GET /

Returns API information:

```json
{
  "message": "GTFS Archive Feed Generator",
  "endpoint": "/generate"
}
```

### GET /generate

Generates archived_feeds.txt content from MobilityDatabase for any feed.

**Query Parameters:**

- `feed_id` (optional): Mobility Database feed ID (e.g., `mdb-503`). Defaults to MBTA (`mdb-503`).

**Examples:**

```bash
# Get MBTA feed (default)
curl http://localhost:8000/generate

# Get any other feed by ID
curl http://localhost:8000/generate?feed_id=mdb-123
```

**Response (200):**

```json
{
  "content": "feed_start_date,feed_end_date,feed_version,archive_url,archive_note\n20251107,20251213,...",
  "count": 150,
  "feed_id": "mdb-503"
}
```

**Response (400 - Invalid Feed ID):**

```json
{
  "error": "Invalid feed ID format: invalid-id. Expected format: mdb-123",
  "feed_id": "invalid-id"
}
```

**Response (404 - No Data):**

```json
{
  "error": "No datasets found for this feed ID",
  "feed_id": "mdb-503",
  "hint": "Verify the feed ID exists at https://mobilitydatabase.org"
}
```

**Response (500 - Server Error):**

```json
{
  "error": "Unauthorized: API key required. Set MOBILITY_DB_REFRESH_TOKEN environment variable.",
  "message": "Failed to generate archived feeds",
  "feed_id": "mdb-503"
}
```

### GET /download

Downloads the archived_feeds.txt content as a CSV file with proper download headers.

**Query Parameters:**

- `feed_id`: Mobility Database feed ID (e.g., `mdb-503`).

**Examples:**

```bash
# Download MBTA feed
curl http://localhost:8000/download?feed_id=mdb-503 -o archived_feeds.txt
```

**Response (200):**

- **Content-Type:** `text/csv`
- **Content-Disposition:** `attachment; filename="archived_feeds_{feed_id}.txt"`
- **Body:** Raw CSV content

**Response (400/404/500):**
Same JSON error format as `/generate` endpoint.

## Usage Examples

### Fetch MBTA archive

```bash
curl http://localhost:8000/generate?feed_id=mdb-503
```

### Fetch any feed by ID

```bash
# Example: Get data for feed mdb-123
curl http://localhost:8000/generate?feed_id=mdb-123
```

### Generate archived_feeds.txt file

The `/generate` endpoint returns archived feed data as CSV content. Here's an example of the output:

```bash
curl -s http://localhost:8000/generate | jq -r '.content' | head -5
```

**Example output:**

```csv
feed_start_date,feed_end_date,feed_version,archive_url,archive_note
20251107,20251213,2025-11-14T17:17:24+00:00,https://storage.googleapis.com/storage/v1/b/mdb-latest/o/mdb-503.zip,
20251004,20251106,2025-10-09T12:30:15+00:00,https://storage.googleapis.com/storage/v1/b/mdb-latest/o/mdb-503.zip,
20250905,20251003,2025-09-05T08:45:00+00:00,https://storage.googleapis.com/storage/v1/b/mdb-latest/o/mdb-503.zip,
```

### Save archived_feeds.txt to file

Use the `/download` endpoint to save directly to a file:

```bash
# Download MBTA archived feeds
curl http://localhost:8000/download -o archived_feeds.txt

# Download for specific feed ID
curl http://localhost:8000/download?feed_id=mdb-456 -o archived_feeds_456.txt
```

Or use `/generate` with jq to extract content:

```bash
curl -s http://localhost:8000/generate?feed_id=mdb-503 | jq -r '.content' > archived_feeds.txt
```

### With authentication (Python)

```bash
MOBILITY_DB_REFRESH_TOKEN="your-token" \
  python -c "from app import fetch_datasets, format_archived_feeds; \
  datasets = fetch_datasets('mdb-503'); \
  print(format_archived_feeds(datasets))"
```

### Finding feed IDs

To find feed IDs for different transit agencies, visit [MobilityDatabase.org](https://mobilitydatabase.org) and search for your transit agency. The feed ID will be in the format `mdb-XXX` or `tld-xxx`.

## Deployment to AWS Lambda

1. Configure your AWS credentials:

```bash
aws configure
```

2. Deploy using Chalice:

```bash
MOBILITY_DB_REFRESH_TOKEN="your-token" chalice deploy
```

3. Set environment variable in Lambda console:
   - Add `MOBILITY_DB_REFRESH_TOKEN` to environment variables

## Configuration

### Environment Variables

- `MOBILITY_DB_REFRESH_TOKEN` (required for API access): Your MobilityDatabase access token

### Constants

Edit `constants.py` to change:

- `MOBILITY_DB_API` - MobilityDatabase API base URL
- `MOBILITY_DB_REFRESH_TOKEN` - MobilityDatabase API Key

## Testing

Run unit tests:

```bash
pytest test_app.py -v
```

Test API integration:

```bash
MOBILITY_DB_REFRESH_TOKEN="your-token" python test_api.py
```

## Data Format

The generated CSV follows the MBTA's archived_feeds.txt format:

| Column          | Format        | Example                        |
| --------------- | ------------- | ------------------------------ |
| feed_start_date | YYYYMMDD      | 20251107                       |
| feed_end_date   | YYYYMMDD      | 20251213                       |
| feed_version    | ISO timestamp | 2025-11-14T17:17:24+00:00      |
| archive_url     | HTTP URL      | <https://example.com/feed.zip> |
| archive_note    | Text          | Service changes, notes         |

## Troubleshooting

### 401 Unauthorized

- Make sure `MOBILITY_DB_REFRESH_TOKEN` environment variable is set
- Verify your token is still valid (tokens may expire)
- Get a new access token from mobilitydatabase.org

### 404 No datasets found

- Check that the feed ID exists
- Verify the feed has published datasets

### 500 Request Entity Too Large

- Usually means the API response is too large
- Try filtering datasets by date range (not yet implemented)
