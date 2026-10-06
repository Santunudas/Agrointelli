"""Optional MongoDB-backed account registration and cookie sessions."""

import hashlib
import hmac
import logging
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

SESSION_COOKIE = "agro_session"
CSRF_COOKIE = "agro_csrf"
SESSION_DAYS = 14
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_HASHER = PasswordHasher()
_DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(24))
_store_lock = threading.Lock()
_store_cache: tuple[str, "AuthStore"] | None = None


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    state: str = Field(min_length=1, max_length=100)
    crops: list[str] = Field(min_length=1, max_length=20)

    @field_validator("name", "state", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address")
        return normalized

    @field_validator("name", "state")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("crops")
    @classmethod
    def normalize_crops(cls, value: list[str]) -> list[str]:
        crops: list[str] = []
        seen: set[str] = set()
        for crop in value:
            normalized = crop.strip()
            if not normalized:
                continue
            if len(normalized) > 80:
                raise ValueError("Each crop name must be 80 characters or fewer")
            key = normalized.casefold()
            if key not in seen:
                crops.append(normalized)
                seen.add(key)
        if not crops:
            raise ValueError("Add at least one crop")
        return crops


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address")
        return normalized


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    crops: list[str] = Field(min_length=1, max_length=20)

    @field_validator("name", "state", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("name", "state")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("crops")
    @classmethod
    def normalize_crops(cls, value: list[str]) -> list[str]:
        return RegisterRequest.normalize_crops(value)


class AuthStore:
    def __init__(self, client: MongoClient, database_name: str) -> None:
        database = client[database_name]
        self.client = client
        self.users: Collection = database["users"]
        self.sessions: Collection = database["sessions"]
        self.users.create_index([("email", ASCENDING)], unique=True)
        self.sessions.create_index([("token_hash", ASCENDING)], unique=True)
        self.sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)


def get_auth_store() -> AuthStore:
    global _store_cache
    uri = os.environ.get("MONGODB_URI", "").strip()
    if not uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account storage is not configured. Set MONGODB_URI to enable registration and login.",
        )
    database_name = os.environ.get("MONGODB_DATABASE", "agrointelli")
    cache_key = f"{uri}\0{database_name}"
    if _store_cache and _store_cache[0] == cache_key:
        return _store_cache[1]

    with _store_lock:
        if _store_cache and _store_cache[0] == cache_key:
            return _store_cache[1]
        client = MongoClient(uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
        try:
            store = AuthStore(client, database_name)
        except PyMongoError:
            client.close()
            raise
        if _store_cache:
            _store_cache[1].client.close()
        _store_cache = (cache_key, store)
        return store


def _handle_database_error(error: PyMongoError) -> HTTPException:
    logger.exception("Authentication database operation failed", exc_info=error)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Account service is temporarily unavailable. Please try again later.",
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": user["name"],
        "email": user["email"],
        "state": user["state"],
        "crops": user["crops"],
        "created_at": user["created_at"].isoformat(),
    }


def _set_session_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    secure = os.environ.get("AUTH_COOKIE_SECURE", "true").strip().lower() not in {"0", "false", "no"}
    max_age = SESSION_DAYS * 24 * 60 * 60
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/auth",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="strict",
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    secure = os.environ.get("AUTH_COOKIE_SECURE", "true").strip().lower() not in {"0", "false", "no"}
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=secure, samesite="lax", path="/auth")
    response.delete_cookie(CSRF_COOKIE, httponly=False, secure=secure, samesite="strict", path="/")


def _require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin or origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-origin request rejected")


def _require_csrf(request: Request, session: dict[str, Any]) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    header_token = request.headers.get("x-csrf-token", "")
    if (
        not cookie_token
        or not header_token
        or not hmac.compare_digest(cookie_token, header_token)
        or not hmac.compare_digest(cookie_token, session["csrf_token"])
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing CSRF token")


def _current_session(request: Request, store: AuthStore) -> tuple[dict[str, Any], dict[str, Any]]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in")
    now = datetime.now(timezone.utc)
    session = store.sessions.find_one({"token_hash": _token_hash(token), "expires_at": {"$gt": now}})
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in")
    user = store.users.find_one({"_id": session["user_id"]})
    if not user:
        store.sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in")
    return user, session


def _create_session(store: AuthStore, user: dict[str, Any], response: Response) -> None:
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    store.sessions.insert_one({
        "user_id": user["_id"],
        "token_hash": _token_hash(session_token),
        "csrf_token": csrf_token,
        "created_at": created_at,
        "expires_at": created_at + timedelta(days=SESSION_DAYS),
    })
    _set_session_cookies(response, session_token, csrf_token)


@router.get("/status")
def auth_status() -> dict[str, bool]:
    return {"configured": bool(os.environ.get("MONGODB_URI", "").strip())}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterRequest, response: Response) -> dict[str, Any]:
    _require_same_origin(request)
    try:
        store = get_auth_store()
        now = datetime.now(timezone.utc)
        user = {
            "name": payload.name,
            "email": payload.email,
            "password_hash": PASSWORD_HASHER.hash(payload.password),
            "state": payload.state,
            "crops": payload.crops,
            "created_at": now,
            "email_verified": False,
        }
        result = store.users.insert_one(user)
        user["_id"] = result.inserted_id
        _create_session(store, user, response)
        return {"user": _public_user(user)}
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    except PyMongoError as error:
        raise _handle_database_error(error) from error


@router.post("/login")
def login(request: Request, payload: LoginRequest, response: Response) -> dict[str, Any]:
    _require_same_origin(request)
    try:
        store = get_auth_store()
        user = store.users.find_one({"email": payload.email})
        password_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
        try:
            password_ok = PASSWORD_HASHER.verify(password_hash, payload.password)
        except (VerifyMismatchError, VerificationError):
            password_ok = False
        if not user or not password_ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")
        _create_session(store, user, response)
        return {"user": _public_user(user)}
    except PyMongoError as error:
        raise _handle_database_error(error) from error


@router.get("/me")
def get_me(request: Request) -> dict[str, Any]:
    if not request.cookies.get(SESSION_COOKIE):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in")
    try:
        user, _ = _current_session(request, get_auth_store())
        return {"user": _public_user(user)}
    except PyMongoError as error:
        raise _handle_database_error(error) from error


@router.patch("/me")
def update_me(request: Request, payload: ProfileUpdateRequest) -> dict[str, Any]:
    _require_same_origin(request)
    try:
        store = get_auth_store()
        user, session = _current_session(request, store)
        _require_csrf(request, session)
        store.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"name": payload.name, "state": payload.state, "crops": payload.crops}},
        )
        user.update({"name": payload.name, "state": payload.state, "crops": payload.crops})
        return {"user": _public_user(user)}
    except PyMongoError as error:
        raise _handle_database_error(error) from error


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    _require_same_origin(request)
    try:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            store = get_auth_store()
            session = store.sessions.find_one({"token_hash": _token_hash(token)})
            if session:
                _require_csrf(request, session)
                store.sessions.delete_one({"_id": session["_id"]})
        _clear_session_cookies(response)
        return {"ok": True}
    except PyMongoError as error:
        raise _handle_database_error(error) from error
