import requests
import time
from typing import Dict, Union

# MobilityDatabase token endpoint
TOKEN_ENDPOINT = "https://api.mobilitydatabase.org/v1/tokens"

# Token cache to avoid refreshing on every call
_token_cache: Dict[str, Union[None, str, float]] = {"access_token": None, "expires_at": None}


def refresh_access_token(refresh_token):
    """
    Exchange a refresh token for a new access token via MobilityDatabase token endpoint.

    Args:
        refresh_token (str): MobilityDatabase refresh token

    Returns:
        str: New access token

    Raises:
        Exception: If token refresh fails
    """
    try:
        if not refresh_token or len(refresh_token) < 10:
            raise Exception("Invalid refresh token format")

        payload = {"refresh_token": refresh_token}

        response = requests.post(TOKEN_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))  # Default to 1 hour

        if not access_token:
            raise Exception("No access token in response")

        # Cache the token with expiration time
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = (
            time.time() + expires_in - 60
        )  # Refresh 60 seconds before expiry

        return access_token

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to refresh access token: {str(e)}")
    except Exception as e:
        raise Exception(f"Error refreshing token: {str(e)}")


def get_valid_access_token(refresh_token):
    """
    Get a valid access token, validating if necessary.

    Args:
        refresh_token (str): MobilityDatabase refresh token

    Returns:
        str: Valid access token
    """
    # Check if cached token is still valid
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if time.time() < _token_cache["expires_at"]:
            return _token_cache["access_token"]

    # Token expired or doesn't exist, validate it
    return refresh_access_token(refresh_token)


def get_mobility_db_auth_header(refresh_token):
    """
    Get authorization header for MobilityDatabase API.

    Args:
        refresh_token (str): MobilityDatabase refresh token

    Returns:
        dict: Authorization header with valid token

    Raises:
        Exception: If token validation fails
    """
    access_token = get_valid_access_token(refresh_token)
    return {"Authorization": f"Bearer {access_token}"}
