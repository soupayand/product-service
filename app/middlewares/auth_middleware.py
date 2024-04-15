from fastapi import FastAPI, Request, HTTPException
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from httpx import AsyncClient
from ..utils.cache import async_cache
import jwt
import os
import logging

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
HASHING_ALGORITHM = os.getenv('HASHING_ALGORITHM')
USER_SERVICE_URL = "http://127.0.0.1:3000/user"



class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(content={"detail": "Authorization token missing or malformed"}, status_code=401)

        token: str = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASHING_ALGORITHM])
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(status_code=400, detail="user_id not found in token")
            
            user_info = await get_user_info(user_id)
            request.state.user = user_info

            response = await call_next(request)
            
        except jwt.PyJWTError as e:
            logger.error("Invalid Token", exc_info=True)
            return JSONResponse(content={"detail": "Invalid Token"}, status_code=401)
        except HTTPException as e:
            logger.error(e.detail, exc_info=True)
            return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)
        except Exception as e:
            logger.error(str(e), exc_info=True)
            return JSONResponse(content={"detail": "Server error"}, status_code=500)

        return response

async def get_user_info(user_id: str):
    user_info = await async_cache.get(user_id)
    if not user_info:
        try:
            async with AsyncClient() as client:
                response = await client.get(f"{USER_SERVICE_URL}/{user_id}")
                response.raise_for_status()
                user_info = response.json()["data"]
                await async_cache.set(user_id, user_info, ttl=900)
        except Exception as e:
            logger.error("Unable to fetch user info from user service", exc_info=True, extra={"user_id": user_id})
            raise HTTPException(status_code=500, detail="Failed to fetch user information")
    return user_info