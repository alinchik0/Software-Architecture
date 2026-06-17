# api_gateway/routers/auth.py
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging
import grpc

import sys
import os

# Настраиваем пути
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api_gateway.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, MessageResponse
from api_gateway.grpc_client import AuthGRPCClient
from shared.redis_cache import is_token_blacklisted

log = logging.getLogger("gateway.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register_user(request: RegisterRequest):
	"""Регистрация нового пользователя."""
	log.info(f"Register request: {request.email}")
	client = AuthGRPCClient()
	try:
		response = client.register(request.email, request.password)
		log.info(f"Register response: success={response.success}, message={response.message}")

		if not response.success:
			# Если регистрация не удалась, возвращаем 400
			raise HTTPException(status_code=400, detail=response.message)

		return MessageResponse(
			success=response.success,
			message=response.message,
			user_id=response.user_id
		)
	except grpc.RpcError as e:
		log.error(f"gRPC Register error: {e.code()} - {e.details()}")
		raise HTTPException(status_code=503, detail=f"gRPC error: {e.details()}")
	except HTTPException:
		raise
	except Exception as e:
		log.error(f"Register error: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
	finally:
		client.close()


@router.post("/login", response_model=TokenResponse)
async def login_user(request: LoginRequest):
	"""Логин пользователя."""
	log.info(f"Login request: {request.email}")
	client = AuthGRPCClient()
	try:
		response = client.login(request.email, request.password)
		log.info(f"Login response: success={response.success}, message={response.message}")

		if not response.success:
			# Если логин не удался, возвращаем 401
			raise HTTPException(status_code=401, detail=response.message)

		return TokenResponse(
			access_token=response.access_token,
			user_id=response.user_id
		)
	except grpc.RpcError as e:
		log.error(f"gRPC Login error: {e.code()} - {e.details()}")
		raise HTTPException(status_code=503, detail=f"gRPC error: {e.details()}")
	except HTTPException:
		raise
	except Exception as e:
		log.error(f"Login error: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
	finally:
		client.close()


@router.post("/logout", response_model=MessageResponse)
async def logout_user(authorization: Optional[str] = Header(None)):
	"""Logout пользователя."""
	log.info(f"Logout request, auth header present: {authorization is not None}")
	if not authorization or not authorization.startswith("Bearer "):
		raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

	token = authorization[7:]

	try:
		if await is_token_blacklisted(token):
			return MessageResponse(success=True, message="Already logged out")
	except Exception as e:
		log.warning(f"Blacklist check failed: {e}")

	client = AuthGRPCClient()
	try:
		response = client.logout(token)
		return MessageResponse(
			success=response.success,
			message=response.message
		)
	except grpc.RpcError as e:
		log.error(f"gRPC Logout error: {e.code()} - {e.details()}")
		raise HTTPException(status_code=503, detail=f"gRPC error: {e.details()}")
	except Exception as e:
		log.error(f"Logout error: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
	finally:
		client.close()