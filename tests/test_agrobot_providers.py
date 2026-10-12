import json
import os
import unittest
from unittest.mock import patch

from app.agrobot import AgroBotEngine, AgroBotProviderError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.payload


class AgroBotProviderTests(unittest.TestCase):
    def setUp(self):
        self.engine = AgroBotEngine()

    def test_configured_model_answers_before_local_knowledge(self):
        with (
            patch.dict(os.environ, {"AGROBOT_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}),
            patch.object(self.engine, "_try_llm_generation", return_value="AI-generated response") as generate,
        ):
            result = self.engine.answer_query("How to control rice stem borer")

        self.assertEqual(result["reply"], "AI-generated response")
        self.assertEqual(result["category"], "AI Farm Advisory")
        generate.assert_called_once()

    def test_gemini_request_uses_system_instruction_and_diagnosis_context(self):
        response = FakeResponse({
            "candidates": [{"content": {"parts": [{"text": "Check the lower leaves first."}]}}]
        })
        with (
            patch.dict(
                os.environ,
                {"AGROBOT_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"},
                clear=True,
            ),
            patch("app.agrobot.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            answer = self.engine._try_llm_generation(
                "What should I do?",
                "en",
                "Tomato___Early_blight",
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(answer, "Check the lower leaves first.")
        self.assertIn("gemini-2.5-flash:generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        self.assertIn("not a confirmed diagnosis", payload["contents"][0]["parts"][0]["text"])

    def test_groq_request_uses_chat_completions_format(self):
        response = FakeResponse({
            "choices": [{"message": {"content": "Inspect the crop and improve airflow."}}]
        })
        with (
            patch.dict(
                os.environ,
                {
                    "AGROBOT_PROVIDER": "groq",
                    "GROQ_API_KEY": "test-key",
                    "GROQ_MODEL": "example-model",
                },
                clear=True,
            ),
            patch("app.agrobot.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            answer = self.engine._try_llm_generation("How do I help my crop?", "en")

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(answer, "Inspect the crop and improve airflow.")
        self.assertEqual(payload["model"], "example-model")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(len(payload["messages"]), 2)

    def test_provider_errors_are_not_replaced_with_offline_answers(self):
        with (
            patch.dict(os.environ, {"AGROBOT_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}),
            patch.object(
                self.engine,
                "_try_llm_generation",
                side_effect=AgroBotProviderError("Gemini could not answer."),
            ),
            self.assertRaisesRegex(AgroBotProviderError, "Gemini could not answer"),
        ):
            self.engine.answer_query("Rice crop advice")

    def test_no_provider_key_keeps_offline_answers_available(self):
        with patch.dict(os.environ, {}, clear=True):
            result = self.engine.answer_query("hello")

        self.assertTrue(result["ok"])
        self.assertIn("reply", result)


if __name__ == "__main__":
    unittest.main()
