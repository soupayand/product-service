from sqlalchemy.exc import NoResultFound, IntegrityError
from ..utils.context import user_info_context
from ..models.item import Item
from typing import List
import logging

logger = logging.getLogger(__name__)

class ItemService:
    def __init__(self, async_session):
        self.async_session = async_session

    async def add_item(self, item_data: dict) -> dict:
        role = user_info_context.get("role")
        if role != "merchant":
            raise AttributeError("User is not a merchant. Cannot add new item.")

        owner_id = user_info_context.get("id")
        if not owner_id:
            raise ValueError("User ID is missing from the user info context.")

        new_item = Item(**item_data, owner_id=owner_id)
        attempts = 2
        async with self.async_session() as session:
            for attempt in range(1, attempts + 1):
                try:
                    session.add(new_item)
                    await session.commit()
                    logger.info("New item added", extra={"item": new_item.to_dict()})
                    return new_item.to_dict()
                except IntegrityError as e:
                    await session.rollback()
                    if attempt == attempts:
                        logger.error("Failed to add item after retries due to version conflicts", extra={"item": new_item.to_dict()})
                        raise e from None
                    logger.info("Retrying to add item due to version conflict", extra={"item": new_item.to_dict()})
                except Exception as e:
                    await session.rollback()
                    logger.error("Error adding new item", extra={"item": new_item.to_dict()})
                    raise e

    async def get_items(self, item_ids: List[int] = None) -> dict:
        async with self.async_session() as session:
            try:
                if item_ids is None:
                    owner_id = user_info_context.get("id")
                    items = await session.execute(select(Item).where(Item.owner_id == owner_id))
                else:
                    items = await session.execute(select(Item).where(Item.id.in_(item_ids)))
                
                items = items.scalars().all()
                return {"items": [item.to_dict() for item in items]}
            except Exception as e:
                logger.error("Error fetching items using item_ids", extra={"item_ids": item_ids})
                raise e

    async def update_item(self, item_data: dict) -> dict:
        attempts = 2
        user_id = user_info_context.get("id")
        async with self.async_session() as session:
            try:
                item = await session.get(Item, item_id)
                if not item or item.owner_id != user_id:
                    raise ValueError("Unauthorized or item not found")

                for attempt in range(1, attempts + 1):
                    try:
                        for key, value in item_data.items():
                            if key in item.__table__.columns.keys() and key not in ['id', 'owner_id']:
                                setattr(item, key, value)
                        await session.commit()
                        return item.to_dict()
                    except IntegrityError as e:
                        await session.rollback()
                        if attempt == attempts:
                            logger.error("Failed to update item after retries due to version conflicts", extra={"item": item.to_dict()})
                            raise e from None
                        logger.debug("Retrying to update item due to version conflict", extra={"item": item.to_dict()})

                    except Exception as e:
                        await session.rollback()
                        logger.error("Error updating item", extra={"item": item.to_dict()})
                        raise e
            except Exception as e:
                logger.error("Error updating item", extra={"item": item_data})
                raise e
