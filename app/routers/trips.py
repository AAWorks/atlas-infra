from fastapi import APIRouter, Request, HTTPException, Body
from app.utils.auth import get_current_user_id

import app.services.trips as trips


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
    responses={404: {"description": "Not found"}}
)


@router.get("")
def get_trips(request: Request):
    try:
        user_id = get_current_user_id(request)
        res = trips.get_trips(user_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
def create_trip():
    return trips.create_trip()


@router.get("/{id}")
def get_trip(id: str):
    return trips.get_trip(id)


@router.patch("/{id}")
def update_trip(id: str):
    return trips.update_trip(id)


@router.get("/{id}/itinerary")
def get_itinerary(id: str):
    return trips.get_itinerary(id)


router.post("/{id}/items")
def create_itinerary_item(id: str):
    return trips.create_itinerary_item(id)


@router.get("/{id}/budget")
def get_budget(id: str):
    return trips.get_budget(id)


@router.post("/{id}/budget")
def create_budget_entry(id: str):
    return trips.create_budget_entry(id)


@router.post("/{id}/export?format=md|html|pdf")
def export_trip(id: str, format: str):
    return trips.export_trip(id, format)