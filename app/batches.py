"""MongoDB-backed crop visit timelines and per-image batch inference."""

import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator
from pymongo.errors import PyMongoError

from app.auth import get_authenticated_user, _handle_database_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batches", tags=["batch processing"])
MAX_BATCH_IMAGES = 20
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class BatchCreateRequest(BaseModel):
    crop_name: str = Field(min_length=1, max_length=80)
    field_name: str = Field(min_length=1, max_length=100)

    @field_validator("crop_name", "field_name", mode="before")
    @classmethod
    def strip_names(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("crop_name", "field_name")
    @classmethod
    def reject_blank_names(cls, value: str) -> str:
        if not value:
            raise ValueError("This field cannot be blank")
        return value


def _iso_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _serialize_batch(batch: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(batch["_id"]),
        "crop_name": batch["crop_name"],
        "field_name": batch["field_name"],
        "created_at": _iso_timestamp(batch["created_at"]),
        "result_count": batch["result_count"],
        "results": [
            {
                **result,
                "analyzed_at": _iso_timestamp(result["analyzed_at"]),
            }
            for result in batch.get("results", [])
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_batch(payload: BatchCreateRequest, request: Request) -> dict[str, Any]:
    user, store = get_authenticated_user(request, require_csrf=True)
    now = datetime.now(timezone.utc)
    document = {
        "user_id": user["_id"],
        "crop_name": payload.crop_name,
        "crop_key": payload.crop_name.casefold(),
        "field_name": payload.field_name,
        "field_key": payload.field_name.casefold(),
        "created_at": now,
        "result_count": 0,
        "results": [],
    }
    try:
        inserted = store.batches.insert_one(document)
    except PyMongoError as error:
        raise _handle_database_error(error) from error
    return {
        "id": str(inserted.inserted_id),
        "crop_name": payload.crop_name,
        "field_name": payload.field_name,
        "created_at": _iso_timestamp(now),
    }


@router.post("/{batch_id}/images")
async def analyze_batch_image(
    batch_id: str,
    request: Request,
    file: UploadFile = File(...),
    field_mode: bool = Query(True, description="Enable Field Mode confidence thresholding"),
) -> dict[str, Any]:
    user, store = get_authenticated_user(request, require_csrf=True)
    if not ObjectId.is_valid(batch_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    try:
        batch = store.batches.find_one({"_id": ObjectId(batch_id), "user_id": user["_id"]})
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
        if batch["result_count"] >= MAX_BATCH_IMAGES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A batch can contain at most {MAX_BATCH_IMAGES} images",
            )

        filename = (file.filename or "leaf").replace("\\", "/").split("/")[-1][:255]
        extension = os.path.splitext(filename)[1].lower()
        if extension not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Upload a JPG, PNG, BMP, or WEBP image",
            )

        content = await file.read(MAX_IMAGE_BYTES + 1)
        if not content:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The image is empty")
        if len(content) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Each image must be 10 MB or smaller",
            )

        descriptor, temp_path = tempfile.mkstemp(suffix=extension)
        try:
            with os.fdopen(descriptor, "wb") as image_file:
                image_file.write(content)
            try:
                with Image.open(temp_path) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError, ValueError) as error:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The uploaded file is not a readable image",
                ) from error

            try:
                result = request.app.state.disease_engine.predict(temp_path, field_mode=field_mode)
            except Exception as error:
                logger.exception("Batch image inference failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Image analysis failed. Please try again.",
                ) from error
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        analyzed_at = datetime.now(timezone.utc)
        stored_result = {
            **result,
            "filename": filename,
            "analyzed_at": analyzed_at,
            "top3": [list(item) for item in result["top3"]],
        }
        update = store.batches.update_one(
            {
                "_id": ObjectId(batch_id),
                "user_id": user["_id"],
                "result_count": {"$lt": MAX_BATCH_IMAGES},
            },
            {"$push": {"results": stored_result}, "$inc": {"result_count": 1}},
        )
        if not update.modified_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A batch can contain at most {MAX_BATCH_IMAGES} images",
            )
    except PyMongoError as error:
        raise _handle_database_error(error) from error

    return {**result, "filename": filename, "analyzed_at": _iso_timestamp(analyzed_at)}


@router.get("")
def list_batches(
    request: Request,
    crop_name: str | None = Query(default=None, max_length=80),
    field_name: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    user, store = get_authenticated_user(request)
    query: dict[str, Any] = {"user_id": user["_id"]}
    if crop_name and crop_name.strip():
        query["crop_key"] = crop_name.strip().casefold()
    if field_name and field_name.strip():
        query["field_key"] = field_name.strip().casefold()
    try:
        batches = store.batches.find(query).sort("created_at", -1).limit(limit)
        return {"batches": [_serialize_batch(batch) for batch in batches]}
    except PyMongoError as error:
        raise _handle_database_error(error) from error
