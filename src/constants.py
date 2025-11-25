import os
from dotenv import load_dotenv

load_dotenv()

# MobilityDatabase API base URL
MOBILITY_DB_API = "https://api.mobilitydatabase.org/v1"

# Get refresh token from environment (.env file)
MOBILITY_DB_REFRESH_TOKEN = os.getenv("MOBILITY_DB_REFRESH_TOKEN", "")
