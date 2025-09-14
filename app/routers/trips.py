"""
Trips Router
"""

from fastapi import APIRouter, Request, HTTPException

import app.services.trips as trips
from app.utils.auth import get_current_user_id


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
    responses={404: {"description": "Not found"}}
)


@router.get("")
async def get_trips(request: Request):
    """
    Get all user trips (w)
    """
    try:
        user_id = get_current_user_id(request)
        res = await trips.get_trips(user_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_trip(request: Request):
    """
    Create a new trip (w)
    """
    try:
        user_id = get_current_user_id(request)
        trip_data = await request.json()
        res = await trips.create_trip(user_id, trip_data)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
async def get_trip(request : Request, id: str):
    """
    Get a specific trip by ID (w)
    """
    try:
        user_id = get_current_user_id(request)
        res = await trips.get_trip(user_id, id)
        if not res:
            raise HTTPException(status_code=404, detail="Trip not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id}")
async def update_trip(id: str, request: Request):
    """
    Modify trip by ID (w)
    """
    try:
        user_id = get_current_user_id(request)
        trip_data = await request.json()
        res = await trips.update_trip(user_id, id, trip_data)
        if not res:
            raise HTTPException(status_code=404, detail="Trip not found")
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/itinerary")
async def get_itinerary(id: str):
    """
    Get itinerary by trip ID (w)
    """
    try:
        res = await trips.get_itinerary(id)  # Await the itinerary fetching here
        if not res:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/items")
async def create_itinerary_item(id: str, request: Request):
    """
    Create itinerary item by trip ID (w)
    """
    try:
        item_data = await request.json()
        res = await trips.create_itinerary_item(id, item_data)
        if not res:
            raise HTTPException(status_code=404, detail="Trip not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/budget")
async def get_budget(id: str):
    """
    Get budget by trip ID (w)
    """
    try:
        res = await trips.get_budget(id)
        if not res:
            raise HTTPException(status_code=404, detail="Budget not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/budget")
async def create_budget_entry(id: str, request: Request):
    """
    Create a new budget entry by trip ID (w)
    """
    try:
        budget_data = await request.json()
        res = await trips.create_budget_entry(id, budget_data)
        if not res:
            raise HTTPException(status_code=404, detail="Trip not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/export")
async def export_trip(id: str, format: str):
    """
    Export trip by trip ID in different formats: Markdown, HTML, PDF (work in progress)
    """
    if format not in ['md', 'html', 'pdf']:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: md, html, pdf")
    try:
        res = await trips.export_trip(id, format)
        if not res:
            raise HTTPException(status_code=404, detail="Trip not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))