import asyncio
from io import BytesIO
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException
from PIL import Image
from starlette.datastructures import UploadFile
from starlette.requests import Request

from app import batches


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: item[field], reverse=direction < 0)
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        saved = dict(document)
        saved["_id"] = ObjectId()
        self.documents.append(saved)
        return SimpleNamespace(inserted_id=saved["_id"])

    def find_one(self, query):
        for document in self.documents:
            if all(
                document.get(key) == value
                or (isinstance(value, dict) and "$lt" in value and document.get(key, 0) < value["$lt"])
                for key, value in query.items()
            ):
                return document
        return None

    def update_one(self, query, update):
        document = self.find_one(query)
        if not document:
            return SimpleNamespace(modified_count=0)
        document["results"].append(update["$push"]["results"])
        document["result_count"] += update["$inc"]["result_count"]
        return SimpleNamespace(modified_count=1)

    def find(self, query):
        documents = [
            item for item in self.documents
            if all(item.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(documents)


class BatchEndpointTests(unittest.TestCase):
    def setUp(self):
        self.user = {"_id": ObjectId()}
        self.store = SimpleNamespace(batches=FakeCollection())
        self.auth_patch = patch(
            "app.batches.get_authenticated_user",
            return_value=(self.user, self.store),
        )
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    @staticmethod
    def make_request():
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/batches",
            "raw_path": b"/batches",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "app": SimpleNamespace(state=SimpleNamespace(disease_engine=None)),
        }
        return Request(scope)

    def test_batch_names_are_trimmed_and_nonblank(self):
        payload = batches.BatchCreateRequest(crop_name="  Tomato ", field_name=" North plot ")
        self.assertEqual(payload.crop_name, "Tomato")
        self.assertEqual(payload.field_name, "North plot")
        with self.assertRaises(ValueError):
            batches.BatchCreateRequest(crop_name=" ", field_name="North plot")

    def test_create_batch_and_list_filtered_history(self):
        first = batches.create_batch(
            batches.BatchCreateRequest(crop_name="Tomato", field_name="North plot"),
            self.make_request(),
        )
        batches.create_batch(
            batches.BatchCreateRequest(crop_name="Rice", field_name="South plot"),
            self.make_request(),
        )

        result = batches.list_batches(
            self.make_request(),
            crop_name=" TOMATO ",
            field_name="north plot",
            limit=10,
        )

        self.assertEqual(len(result["batches"]), 1)
        self.assertEqual(result["batches"][0]["id"], first["id"])
        self.assertEqual(result["batches"][0]["result_count"], 0)

    def test_analyze_image_persists_result_and_timestamp(self):
        created = batches.create_batch(
            batches.BatchCreateRequest(crop_name="Tomato", field_name="North plot"),
            self.make_request(),
        )
        request = self.make_request()
        request.app.state.disease_engine = SimpleNamespace(
            predict=lambda _path, field_mode: {
                "prediction": "Tomato___Early_blight",
                "confidence": 0.91,
                "top3": [("Tomato___Early_blight", 0.91)],
                "mode": "high confidence" if field_mode else "lab mode",
                "quality": {"ok": True, "warnings": []},
                "severity_proxy": {"severity": "early/moderate", "lesion_ratio": 0.12},
                "advice": "Monitor the crop.",
            }
        )
        image_buffer = BytesIO()
        Image.new("RGB", (16, 16), color="green").save(image_buffer, format="PNG")
        image_buffer.seek(0)
        upload = UploadFile(filename="leaf.png", file=image_buffer)

        result = asyncio.run(
            batches.analyze_batch_image(
                created["id"],
                request,
                upload,
                field_mode=True,
            )
        )

        saved = self.store.batches.documents[0]
        self.assertEqual(result["filename"], "leaf.png")
        self.assertEqual(saved["result_count"], 1)
        self.assertEqual(saved["results"][0]["prediction"], "Tomato___Early_blight")
        self.assertIsInstance(saved["results"][0]["analyzed_at"], datetime)
        self.assertEqual(saved["results"][0]["analyzed_at"].tzinfo, timezone.utc)

    def test_cannot_read_or_append_to_another_farmers_batch(self):
        created = batches.create_batch(
            batches.BatchCreateRequest(crop_name="Tomato", field_name="North plot"),
            self.make_request(),
        )
        self.user["_id"] = ObjectId()
        result = batches.list_batches(
            self.make_request(),
            crop_name=None,
            field_name=None,
            limit=10,
        )
        self.assertEqual(result["batches"], [])
        with self.assertRaises(HTTPException) as not_found:
            asyncio.run(
                batches.analyze_batch_image(
                    created["id"],
                    self.make_request(),
                    UploadFile(filename="leaf.png", file=BytesIO(b"")),
                )
            )
        self.assertEqual(not_found.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
