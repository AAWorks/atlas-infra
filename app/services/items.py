"""
Itinerary Item Service
"""

from app.configs import config
from app.database import client as db_client


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
    response = db_client.table(config.DB_SCHEMA.ITINERARY_ITEM).insert(item).execute()
    return response.data


async def get_itinerary(trip_id: str):
    itinerary = db_client.table(config.DB_SCHEMA.ITINERARY_ITEM).select("*").eq("trip_id", trip_id).order("start_time").execute()
    return itinerary.data