from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv


load_dotenv()
DATABASE_URI = os.getenv("DATABASE_URI")
if DATABASE_URI is None:
    raise ConnectionError("Database URI not present in .env file")

_async_engine = create_async_engine(DATABASE_URI, echo=True)
SESSION = sessionmaker(_async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    async with SESSION() as session:
        yield session
