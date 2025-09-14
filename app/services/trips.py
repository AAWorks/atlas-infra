"""
Trips Service
"""

from supabase import create_client

from app.configs import config

from fastapi import HTTPException

supabase = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_KEY
)


async def get_trips(user_id: str):
    trips = supabase.table(config.DB_SCHEMA.TRIP).select("*").eq("owner_user_id", user_id).execute()
    return trips.data


def create_trip(user_id: str, trip_data: dict):
    try:
        # Prepare the trip data
        trip = {
            "title": trip_data["title"],
            "description": trip_data["description"],
            "start_date": trip_data["start_date"],
            "end_date": trip_data["end_date"],
            "home_currency": trip_data["home_currency"],
            "time_zone": trip_data["time_zone"],
            "notes": trip_data["notes"]
        }

        # Insert the trip into the database synchronously
        response = supabase.table(config.DB_SCHEMA.TRIP).insert({**trip, "owner_user_id": user_id}).execute()

        # Check if the response contains data or if it's empty
        if not response.data or isinstance(response.data, list) and len(response.data) == 0:
            raise Exception(f"Failed to create trip: No data returned.")

        # Return the inserted trip data
        return response.data

    except Exception as e:
        # Handle any errors that occur during the operation
        raise HTTPException(status_code=500, detail=f"Error creating trip: {str(e)}")


