"""
Itinerary Item Service
"""

from app.configs import config
from app.database import client as db_client


async def create_budget_entry(trip_id: str, budget_data: dict):
    """
    Insert query on budget
    """
    entry = {
        "trip_id": trip_id,
        "item_id": budget_data.get("item_id", None),
        "category": budget_data["category"],
        "amount": budget_data["amount"],
        "currency": budget_data["currency"]
    }

    response = db_client.table(
        config.DB_SCHEMA.BUDGET_ENTRY
    ).insert(entry).execute()

    return response.data

async def get_budget(trip_id: str):
    """
    Select query on budget
    """
    budget = db_client.table(
        config.DB_SCHEMA.BUDGET_ENTRY
    ).select("*").eq("trip_id", trip_id).execute()

    return budget.data