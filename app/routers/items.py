from fastapi import APIRouter

import app.services.items as items


router = APIRouter(
    prefix="/items",
    tags=["Items"],
    responses={404: {"description": "Not found"}}
)

@router.patch("/{item_id}")
def update_item(item_id: str):  
    return items.update_item(item_id)


@router.post("/{item_id}/tickets")
def add_ticket_link(item_id: str):
    return items.add_ticket_link(item_id)


@router.post("/{item_id}/attachments")
def add_attachment(item_id: str):
    return items.add_attachment(item_id)
