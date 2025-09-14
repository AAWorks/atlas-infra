from fastapi import APIRouter, HTTPException
import app.services.items as items

router = APIRouter(
    prefix="/items",
    tags=["Items"],
    responses={404: {"description": "Not found"}}
)

@router.patch("/{item_id}")
async def update_item(item_id: str):
    """
    Update an item by ID
    """
    try:
        res = await items.update_item(item_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/tickets")
async def add_ticket_link(item_id: str):
    """
    Add ticket link to an item
    """
    try:
        res = await items.add_ticket_link(item_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/attachments")
async def add_attachment(item_id: str):
    """
    Add attachment to an item
    """
    try:
        res = await items.add_attachment(item_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
