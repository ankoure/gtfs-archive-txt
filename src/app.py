from chalice.app import Chalice, Response, CORSConfig
from utils import validate_feed_id, fetch_datasets, format_archived_feeds

# Allow all origins for CORS
cors_config = CORSConfig(
    allow_origin="*",
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
    max_age=600,
)

app = Chalice(app_name="archived-feeds-api")


@app.route("/")
def index():
    return {"message": "GTFS Archive Feed Generator", "endpoint": "/generate"}


@app.route("/archived_feeds.txt", cors=cors_config)
def archived_feeds_txt():
    """Legacy endpoint that serves archived_feeds.txt directly

    This endpoint exists for backward compatibility with clients that use urljoin()
    to construct the URL, which strips query parameters.

    Query Parameters:
        feed_id (optional): Mobility Database feed ID (e.g., mdb-503).
        filter_null_dates (optional): If 'true', exclude rows with missing feed_start_date or feed_end_date.
    """
    # Just call the download endpoint with the same logic
    return download_archived_feeds()


@app.route("/generate", cors=cors_config)
def generate_archived_feeds():
    """Generate archived_feeds.txt from MobilityDatabase

    Query Parameters:
        feed_id (optional): Mobility Database feed ID (e.g., mdb-503).
        filter_null_dates (optional): If 'true', exclude rows with missing feed_start_date or feed_end_date.
    """
    # Get feed_id from query params, default to MBTA
    filter_null_dates = False
    feed_id = None
    if app.current_request.query_params:
        feed_id = app.current_request.query_params.get("feed_id")
        filter_null_dates = (
            app.current_request.query_params.get("filter_null_dates", "").lower()
            == "true"
        )

    # Validate feed_id format
    is_valid, error_msg = validate_feed_id(feed_id)
    if not is_valid:
        return {"error": error_msg, "feed_id": feed_id}, 400

    try:
        # Fetch datasets for specified feed
        datasets = fetch_datasets(feed_id)

        if not datasets:
            return {
                "error": "No datasets found for this feed ID",
                "feed_id": feed_id,
                "hint": "Verify the feed ID exists at https://mobilitydatabase.org",
            }, 404

        # Generate CSV content
        csv_content = format_archived_feeds(datasets, filter_null_dates)

        return {
            "content": csv_content,
            "count": len(datasets) - 1,  # Exclude header row
            "feed_id": feed_id,
        }

    except Exception as e:
        error_msg = str(e)
        status_code = 500

        # More specific error handling
        if "not found" in error_msg.lower() or "404" in error_msg:
            status_code = 404
            error_msg = f"Feed ID {feed_id} not found in MobilityDatabase"
        elif "unauthorized" in error_msg.lower() or "401" in error_msg:
            status_code = 401

        return {
            "error": error_msg,
            "message": "Failed to generate archived feeds",
            "feed_id": feed_id,
        }, status_code


@app.route("/download", cors=cors_config)
def download_archived_feeds():
    """Download archived_feeds.txt as a file

    Query Parameters:
        feed_id (optional): Mobility Database feed ID (e.g., mdb-503).
        filter_null_dates (optional): If 'true', exclude rows with missing feed_start_date or feed_end_date.

    Returns:
        CSV file with Content-Disposition header for download
    """
    # Get feed_id from query params, default to MBTA
    feed_id = None
    filter_null_dates = False
    if app.current_request.query_params:
        feed_id = app.current_request.query_params.get("feed_id")
        filter_null_dates = (
            app.current_request.query_params.get("filter_null_dates", "").lower()
            == "true"
        )

    # Validate feed_id format
    is_valid, error_msg = validate_feed_id(feed_id)
    if not is_valid:
        return Response(
            body={"error": error_msg, "feed_id": feed_id},
            status_code=400,
            headers={"Content-Type": "application/json"},
        )

    try:
        datasets = fetch_datasets(feed_id)

        if not datasets:
            return Response(
                body={
                    "error": "No datasets found for this feed ID",
                    "feed_id": feed_id,
                    "hint": "Verify the feed ID exists at https://mobilitydatabase.org",
                },
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

        csv_content = format_archived_feeds(datasets, filter_null_dates)

        # Generate filename based on feed_id
        filename = "archived_feeds.txt"

        # Return CSV file with proper headers
        return Response(
            body=csv_content,
            status_code=200,
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )

    except Exception as e:
        error_msg = str(e)
        status_code = 500

        # More specific error handling
        if "not found" in error_msg.lower() or "404" in error_msg:
            status_code = 404
            error_msg = f"Feed ID {feed_id} not found in MobilityDatabase"
        elif "unauthorized" in error_msg.lower() or "401" in error_msg:
            status_code = 401

        return Response(
            body={
                "error": error_msg,
                "message": "Failed to download archived feeds",
                "feed_id": feed_id,
            },
            status_code=status_code,
            headers={"Content-Type": "application/json"},
        )
