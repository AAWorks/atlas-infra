"""
Trips Service
"""

from typing import Optional
from fastapi import HTTPException

from app.configs import config
from app.database import client as db_client


async def get_trips(user_id: str) -> list:
    """
    Select multiple query (trip(s) given user)
    """
    trips = db_client.table(
        config.DB_SCHEMA.TRIP
    ).select("*").eq("owner_user_id", user_id).execute()
    return trips.data


async def create_trip(user_id: str, trip_data: dict):
    """
    Insert query on trips
    """
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

        # Insert the trip into the database
        response = db_client.table(
            config.DB_SCHEMA.TRIP
        ).insert({**trip, "owner_user_id": user_id}).execute()

        # Check if the response contains data or if it's empty
        if not response.data or (
            isinstance(response.data, list) and len(response.data) == 0
        ):
            raise Exception(f"Failed to create trip: No data returned.")

        # Return the inserted trip data
        return response.data

    except Exception as e:
        # Handle any errors that occur during the operation
        raise HTTPException(
            status_code=500,
            detail=f"Error creating trip: {str(e)}"
        )
    

async def get_trip(trip_id: str) -> Optional[dict]:
    """
    Select one query on trips
    """
    trip = db_client.table(
        config.DB_SCHEMA.TRIP
    ).select("*").eq("id", trip_id).execute()
    
    if trip.data is None or (
        isinstance(trip.data, list) and len(trip.data) == 0
    ):
        # no trip found with trip id
        return None
    
    return trip.data[0]


async def update_trip(trip_id: str, trip_data: dict):
    """
    Wrapper over update query on trips
    """
    try:
        updated_trip = {
            key: value for key, value in trip_data.items() if value is not None
        }

        if not updated_trip:
            raise HTTPException(status_code=400, detail="No data to update")

        response = db_client.table(
            config.DB_SCHEMA.TRIP
        ).update(updated_trip).eq("id", trip_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Trip not found or failed to update"
            )

        return response.data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating trip: {str(e)}"
        )


async def get_itinerary(trip_id: str):
    """
    Select multiple on trips, ordered by start
    """
    itinerary = db_client.table(
        config.DB_SCHEMA.ITINERARY_ITEM
    ).select("*").eq("trip_id", trip_id).order("start_time").execute()
    return itinerary.data


async def export_trip_data(trip_id: str):
    """
    Export trip data in html format
    """
    # Fetch trip details
    trip = db_client.table(
        config.DB_SCHEMA.TRIP
    ).select("*").eq("id", trip_id).single().execute()
    if not trip.data:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Fetch itinerary items
    itinerary = db_client.table(
        config.DB_SCHEMA.ITINERARY_ITEM
    ).select("*").eq("trip_id", trip_id).order("start_time").execute()

    # Fetch budget entries
    budget = db_client.table(
        config.DB_SCHEMA.BUDGET_ENTRY
    ).select("*").eq("trip_id", trip_id).execute()

    # Combine all data into a single dictionary
    export_data = {
        "content" : {
            "trip": trip.data,
            "itinerary": itinerary.data,
            "budget": budget.data
        }
    }

    return export_data