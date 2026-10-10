import os
from http.cookies import SimpleCookie
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response

from app import auth


class FakeCollection:
    def __init__(self, unique_field=None):
        self.documents = []
        self.next_id = 1
        self.unique_field = unique_field

    def create_index(self, *_args, **_kwargs):
        return None

    def insert_one(self, document):
        if self.unique_field and any(
            saved.get(self.unique_field) == document.get(self.unique_field)
            for saved in self.documents
        ):
            raise auth.DuplicateKeyError("duplicate key")
        stored = dict(document)
        stored["_id"] = self.next_id
        self.next_id += 1
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def find_one(self, query):
        for document in self.documents:
            if all(
                document.get(key) == value
                or (isinstance(value, dict) and "$gt" in value and document.get(key) > value["$gt"])
                for key, value in query.items()
            ):
                return document
        return None

    def update_one(self, query, update):
        document = self.find_one(query)
        if document:
            document.update(update.get("$set", {}))

    def delete_one(self, query):
        document = self.find_one(query)
        if document:
            self.documents.remove(document)


class FakeStore:
    def __init__(self):
        self.users = FakeCollection(unique_field="email")
        self.sessions = FakeCollection()


class AuthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        self.store_patch = patch("app.auth.get_auth_store", return_value=self.store)
        self.store_patch.start()
        self.env_patch = patch.dict(os.environ, {"AUTH_COOKIE_SECURE": "false"})
        self.env_patch.start()

    def tearDown(self):
        self.store_patch.stop()
        self.env_patch.stop()

    @staticmethod
    def make_request(method="POST", cookies=None, headers=None, include_origin=True, scheme="http"):
        headers = headers or {}
        request_headers = []
        if include_origin and not any(name.lower() == "origin" for name in headers):
            request_headers.append((b"origin", f"{scheme}://testserver".encode()))
        for name, value in headers.items():
            request_headers.append((name.lower().encode(), value.encode()))
        if cookies:
            cookie_header = "; ".join(f"{name}={value}" for name, value in cookies.items())
            request_headers.append((b"cookie", cookie_header.encode()))
        return Request({
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": scheme,
            "path": "/auth/test",
            "raw_path": b"/auth/test",
            "query_string": b"",
            "root_path": "",
            "headers": request_headers,
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        })

    @staticmethod
    def response_cookies(response):
        cookies = SimpleCookie()
        for value in response.headers.getlist("set-cookie"):
            cookies.load(value)
        return {name: morsel.value for name, morsel in cookies.items()}

    def register(self):
        payload = auth.RegisterRequest(
            name="  Test Farmer ",
            email="  Farmer@Example.com ",
            password="a-strong-test-password",
            state=" West Bengal ",
            crops=["Rice", " rice ", "Potato"],
        )
        response = Response()
        result = auth.register(self.make_request(), payload, response)
        response_headers = response.headers.getlist("set-cookie")
        session_header = next(header for header in response_headers if header.startswith(f"{auth.SESSION_COOKIE}="))
        self.assertIn("httponly", session_header.lower())
        self.assertIn("path=/auth", session_header.lower())
        return result["user"], self.response_cookies(response)

    def test_register_login_profile_update_and_logout(self):
        user, cookies = self.register()
        self.assertEqual(user["email"], "farmer@example.com")
        self.assertEqual(user["name"], "Test Farmer")
        self.assertEqual(user["crops"], ["Rice", "Potato"])
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)
        self.assertNotEqual(self.store.users.documents[0]["password_hash"], "a-strong-test-password")
        self.assertEqual(len(self.store.sessions.documents[0]["token_hash"]), 64)
        self.assertNotIn(cookies[auth.SESSION_COOKIE], str(self.store.sessions.documents[0]))

        csrf = cookies[auth.CSRF_COOKIE]
        session = cookies[auth.SESSION_COOKIE]
        updated = auth.update_me(
            self.make_request(
                method="PATCH",
                cookies={auth.CSRF_COOKIE: csrf, auth.SESSION_COOKIE: session},
                headers={"X-CSRF-Token": csrf},
            ),
            auth.ProfileUpdateRequest(name="Updated Farmer", state="Bihar", crops=["Wheat"]),
        )
        self.assertEqual(updated["user"]["name"], "Updated Farmer")
        self.assertEqual(updated["user"]["crops"], ["Wheat"])

        logout_response = Response()
        logout_result = auth.logout(
            self.make_request(
                cookies={auth.CSRF_COOKIE: csrf, auth.SESSION_COOKIE: session},
                headers={"X-CSRF-Token": csrf},
            ),
            logout_response,
        )
        self.assertTrue(logout_result["ok"])
        self.assertEqual(
            auth.get_auth_store().sessions.find_one({"token_hash": auth._token_hash(session)}),
            None,
        )

        login_response = Response()
        login_result = auth.login(
            self.make_request(),
            auth.LoginRequest(email="FARMER@example.com", password="a-strong-test-password"),
            login_response,
        )
        self.assertEqual(login_result["user"]["email"], "farmer@example.com")

    def test_invalid_password_and_duplicate_email_are_rejected(self):
        self.register()
        with self.assertRaises(HTTPException) as duplicate:
            self.register()
        self.assertEqual(duplicate.exception.status_code, 409)

        for email in ("farmer@example.com", "unknown@example.com"):
            with self.subTest(email=email), self.assertRaises(HTTPException) as rejected:
                auth.login(
                    self.make_request(),
                    auth.LoginRequest(email=email, password="wrong-password"),
                    Response(),
                )
            self.assertEqual(rejected.exception.status_code, 401)
            self.assertEqual(rejected.exception.detail, "Email or password is incorrect")

    def test_profile_update_requires_csrf_token(self):
        _, cookies = self.register()
        with self.assertRaises(HTTPException) as rejected:
            auth.update_me(
                self.make_request(
                    method="PATCH",
                    cookies=cookies,
                ),
                auth.ProfileUpdateRequest(name="Updated Farmer", state="Bihar", crops=["Wheat"]),
            )
        self.assertEqual(rejected.exception.status_code, 403)

    def test_authenticated_user_requires_valid_session_and_csrf_for_writes(self):
        with self.assertRaises(HTTPException) as unsigned:
            auth.get_authenticated_user(self.make_request(), require_csrf=True)
        self.assertEqual(unsigned.exception.status_code, 401)

        user, cookies = self.register()
        request = self.make_request(
            cookies=cookies,
            headers={"X-CSRF-Token": cookies[auth.CSRF_COOKIE]},
        )
        current_user, store = auth.get_authenticated_user(request, require_csrf=True)
        self.assertEqual(current_user["email"], user["email"])
        self.assertIs(store, self.store)

        with self.assertRaises(HTTPException) as missing_csrf:
            auth.get_authenticated_user(
                self.make_request(cookies={auth.SESSION_COOKIE: cookies[auth.SESSION_COOKIE]}),
                require_csrf=True,
            )
        self.assertEqual(missing_csrf.exception.status_code, 403)

    def test_register_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            auth.RegisterRequest(
                name="Test Farmer",
                email="farmer@example.com",
                password="short",
                state="West Bengal",
                crops=["Rice"],
            )

    def test_registration_requires_same_origin(self):
        payload = auth.RegisterRequest(
            name="Test Farmer",
            email="farmer@example.com",
            password="a-strong-test-password",
            state="West Bengal",
            crops=["Rice"],
        )
        request_options = (
            {"include_origin": False},
            {"headers": {"Origin": "https://attacker.example"}},
        )
        for options in request_options:
            with self.subTest(options=options):
                with self.assertRaises(HTTPException) as rejected:
                    auth.register(self.make_request(**options), payload, Response())
                self.assertEqual(rejected.exception.status_code, 403)

    def test_https_same_origin_is_accepted_for_tunneled_requests(self):
        auth._require_same_origin(self.make_request(scheme="https", headers={"host": "testserver"}))


if __name__ == "__main__":
    unittest.main()
