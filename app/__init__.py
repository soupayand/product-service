from fastapi import FastAPI
from .middlewares.auth_middleware import AuthMiddleware
from .api.item import router as item_router
from .database.connection import _async_engine
from .models import Base
from dotenv import load_dotenv
import os

def create_app() -> FastAPI:
    
    load_dotenv()
    
    app = FastAPI()

    """
        Add middlewares below
    """
    app.add_middleware(AuthMiddleware)

    """
        Add routes here
    """
    app.include_router(item_router)
    
    @app.on_event("startup")
    async def startup_event():
        async with _async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    return app

