from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.connection import get_db_session
from ..services.item_service import ItemService
from typing import List
import logging 

router = APIRouter()
logger= logging.getLogger(__name__)

@router.post("/item/", status_code=status.HTTP_201_CREATED)
async def create_item(item_data: dict, session: AsyncSession = Depends(get_db_session)):
    try:
        item_service = ItemService(session)
        return await item_service.add_item(item_data)
    except Exception as e:
        logger.error(str(e), exc_info=True, extra={"item": item_data})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"status":"failure","message":"Error adding new item","error" : str(e)})
    
@router.get("/items/", status_code=status.HTTP_200_OK)
async def retrieve_items(item_ids : List[int] = Query(default=None, description="List of item ids"), session: AsyncSession = Depends(get_db_session)):
    try:
        item_service = ItemService(session)
        items = await item_service.get_items(item_ids)
        return items
    except Exception as e:
        logger.error(str(e), exc_info=True, extra={"item_ids": item_ids})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
@router.put("/item/", status_code=status.HTTP_200_OK)
async def update_item(item_data: dict, session: AsyncSession = Depends(get_db_session)):
    try:
        item_service = ItemService(session)
        updated_item = await item_service.update_item(item_data)
        return updated_item
    except Exception as e:
        logger.error(str(e), exc_info=True, extra={"item": item_data})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))