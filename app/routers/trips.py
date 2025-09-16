"""
Trips Router
"""

from fastapi import (
    APIRouter, Request,
    HTTPException, Depends
)

import app.services.trips as trips
from app.dependencies import resolve_user_id


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_trips(user_id: str = Depends(resolve_user_id)):
    """
    Get all user trips (w)
    """
    return await trips.get_trips(user_id)


@router.post("")
async def create_trip(request: Request, user_id: str = Depends(resolve_user_id)):
    """
    Create a new trip (w)
    """
    trip_data = await request.json()
    return await trips.create_trip(user_id, trip_data)


@router.get("/{id}")
async def get_trip(id: str, user_id: str = Depends(resolve_user_id)):
    """
    Get a specific trip by ID (w)
    """
    res = await trips.get_trip(user_id, id)
    if not res:
        raise HTTPException(status_code=404, detail="Trip not found")
    return res


@router.patch("/{id}")
async def update_trip(id: str, request: Request, user_id: str = Depends(resolve_user_id)):
    """
    Modify trip by ID (w)
    """
    trip_data = await request.json()
    res = await trips.update_trip(user_id, id, trip_data)
    if not res:
        raise HTTPException(status_code=404, detail="Trip not found")
    return res


# TODO: review whether or not user_id is needed for the below routes (I believe it should be)


@router.get("/{id}/itinerary")
async def get_itinerary(id: str):
    """
    Get itinerary by trip ID (w)
    """
    res = await trips.get_itinerary(id)
    if not res:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return res


@router.post("/{id}/items")
async def create_itinerary_item(id: str, request: Request):
    """
    Create itinerary item by trip ID (w)
    """
    item_data = await request.json()
    res = await trips.create_itinerary_item(id, item_data)
    if not res:
        raise HTTPException(status_code=404, detail="Trip not found")
    return res


@router.get("/{id}/budget")
async def get_budget(id: str):
    """
    Get budget by trip ID (w)
    """
    res = await trips.get_budget(id)
    if not res:
        raise HTTPException(status_code=404, detail="Budget not found")
    return res


@router.post("/{id}/budget")
async def create_budget_entry(id: str, request: Request):
    """
    Create a new budget entry by trip ID (w)
    """
    budget_data = await request.json()
    res = await trips.create_budget_entry(id, budget_data)
    if not res:
        raise HTTPException(status_code=404, detail="Trip not found")
    return res


@router.post("/{id}/export")
async def export_trip(id: str, format: str):
    """
    Export trip by trip ID in different formats: Markdown, HTML, PDF (work in progress)
    """
    if format not in ["md", "html", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: md, html, pdf")

    res = await trips.export_trip(id, format)
    if not res:
        raise HTTPException(status_code=404, detail="Trip not found")
    return res
