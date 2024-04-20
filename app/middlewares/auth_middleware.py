from fastapi import FastAPI, Request, HTTPException
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from httpx import AsyncClient
from ..utils.cache import async_cache
from ..utils.context import user_info_context
import jwt
import os
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(content={"detail": "Authorization token missing or malformed"}, status_code=401)

        token: str = authorization.split(" ")[1]
        user_info_token = None
        try:
            secret_key = os.getenv("JWT_SECRET_KEY")
            hashing_algo = [os.getenv("HASHING_ALGORITHM")]

            payload = jwt.decode(token,secret_key, algorithms=hashing_algo)
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(status_code=400, detail="user_id not found in token")
            
            user_info = await get_user_info(user_id)
            user_info_token = user_info_context.set(user_info)

            response = await call_next(request)
            
        except jwt.PyJWTError as e:
            logger.error("Invalid Token", exc_info=True)
            return JSONResponse(content={"status": "failure", "message": str(e)}, status_code=401)
        except Exception as e:
            logger.error(str(e), exc_info=True)
            return JSONResponse(content={"status":"failure","message":"Server error"}, status_code=500)
        finally:
            if user_info_token:
                user_info_context.reset(user_info_token)
        return response

async def get_user_info(user_id: str):
    user_info = await async_cache.get(user_id)
    if not user_info:
        try:
            async with AsyncClient() as client:
                user_service_url = os.getenv("USER_SERVICE_URL")
                response = await client.get(f"{user_service_url}/{user_id}")
                response.raise_for_status()
                user_info = response.json()["data"]
                await async_cache.set(user_id, user_info, ttl=900)
        except Exception as e:
            logger.error("Unable to fetch user info from user service", exc_info=True, extra={"user_id": user_id})
            raise HTTPException(status_code=500, detail="Failed to fetch user information")
    return user_info