"""
Trips Service
"""

from supabase import create_client

from app.configs import config

supabase = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_KEY
)

# Get User Trips
async def get_trips(user_id: str):
    trips = supabase.table(config.DB_SCHEMA.TRIP).select("*").eq("owner_user_id", user_id).execute()
    return trips.data
