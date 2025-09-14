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


async def create_trip(user_id: str, trip_data: dict):
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
        response = supabase.table(config.DB_SCHEMA.TRIP).insert({**trip, "owner_user_id": user_id}).execute()

        # Check if the response contains data or if it's empty
        if not response.data or isinstance(response.data, list) and len(response.data) == 0:
            raise Exception(f"Failed to create trip: No data returned.")

        # Return the inserted trip data
        return response.data

    except Exception as e:
        # Handle any errors that occur during the operation
        raise HTTPException(status_code=500, detail=f"Error creating trip: {str(e)}")
    

async def get_trip(user_id : str, trip_id: str):
    trip = supabase.table(config.DB_SCHEMA.TRIP).select("*").eq("owner_user_id", user_id).eq("id", trip_id).execute()
    return trip.data


async def update_trip(user_id: str, trip_id: str, trip_data: dict):
    try:
        updated_trip = {key: value for key, value in trip_data.items() if value is not None}

        if not updated_trip:
            raise HTTPException(status_code=400, detail="No data to update")

        response = supabase.table(config.DB_SCHEMA.TRIP).update(updated_trip).eq("owner_user_id", user_id).eq("id", trip_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Trip not found or failed to update")

        return response.data  

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating trip: {str(e)}")


async def create_itinerary_item(id, item_data):
    item = {
        "trip_id": id,
        "type": item_data["type"],
        "name": item_data.get("name"),
        "link": item_data.get("link", None),
        "cost_amount": item_data.get("cost_amount", None),
        "cost_currency": item_data.get("cost_currency", None),
        "start_time": item_data.get("start_time", None),
        "end_time": item_data.get("end_time", None),
        "all_day": item_data.get("all_day", False),
        "status": item_data.get("status", "planned"),
        "notes": item_data.get("notes", None)
    }
    response = supabase.table(config.DB_SCHEMA.ITINERARY_ITEM).insert(item).execute()
    return response.data


async def get_itinerary(trip_id: str):
    itinerary = supabase.table(config.DB_SCHEMA.ITINERARY_ITEM).select("*").eq("trip_id", trip_id).order("start_time").execute()
    return itinerary.data


async def create_budget_entry(trip_id: str, budget_data: dict):
    entry = {
        "trip_id": trip_id,
        "item_id": budget_data.get("item_id", None),
        "category": budget_data["category"],
        "amount": budget_data["amount"],
        "currency": budget_data["currency"]
    }
    response = supabase.table(config.DB_SCHEMA.BUDGET_ENTRY).insert(entry).execute()
    return response.data

async def get_budget(trip_id: str):
    budget = supabase.table(config.DB_SCHEMA.BUDGET_ENTRY).select("*").eq("trip_id", trip_id).execute()
    return budget.data


async def export_trip_data(trip_id: str):
    # Fetch trip details
    trip = supabase.table(config.DB_SCHEMA.TRIP).select("*").eq("id", trip_id).single().execute()
    if not trip.data:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Fetch itinerary items
    itinerary = supabase.table(config.DB_SCHEMA.ITINERARY_ITEM).select("*").eq("trip_id", trip_id).order("start_time").execute()

    # Fetch budget entries
    budget = supabase.table(config.DB_SCHEMA.BUDGET_ENTRY).select("*").eq("trip_id", trip_id).execute()

    # Combine all data into a single dictionary
    export_data = {
        "trip": trip.data,
        "itinerary": itinerary.data,
        "budget": budget.data
    }

    return export_data