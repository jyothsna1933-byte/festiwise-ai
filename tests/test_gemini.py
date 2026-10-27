"""Test Gemini API integration, error handling, and demo mode fallbacks for FestiWise AI."""

import os
from unittest.mock import patch, MagicMock
from models.schemas import EventInput, PlanRescueRequest
from services.gemini_service import (
    is_gemini_available,
    generate_ai_event_blueprint,
    generate_plan_rescue_advice,
    classify_gemini_error,
    sanitize_api_message,
    verify_gemini_connection
)


def test_missing_credentials_graceful_status():
    """Verify clean reporting when credentials are missing."""
    with patch.dict(os.environ, {}, clear=True):
        available, reason = is_gemini_available()
        assert available is False
        assert "not configured" in reason.lower() or "missing" in reason.lower()


def test_missing_credentials_fallback_blueprint():
    """Verify that when API key is missing, system falls back safely without crashing."""
    with patch.dict(os.environ, {}, clear=True):
        inp = EventInput(
            event_name="Simulated Birthday Bash",
            event_category="Birthday",
            event_date="2026-11-30",
            city_location="Pune",
            guest_count=40,
            total_budget=30000.0,
            currency="INR"
        )
        blueprint = generate_ai_event_blueprint(inp)

        assert blueprint["used_live_ai"] is False
        assert "Demonstration" in blueprint["model_used"]
        assert blueprint["creative"].recommended_theme is not None
        assert len(blueprint["day_schedule"]) > 0
        assert len(blueprint["vendor_guidance"]) > 0


def test_api_failure_and_malformed_json_fallback():
    """Verify that if Gemini returns invalid JSON or fails with an API error,

    the service falls back gracefully without exposing crashes to the user.
    """
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_test_key"}):
        with patch("services.gemini_service.get_gemini_client") as mock_client:
            # Mock client to throw API exception
            mock_inst = MagicMock()
            mock_inst.models.generate_content.side_effect = Exception("API Quota Exceeded (HTTP 429)")
            mock_client.return_value = mock_inst

            inp = EventInput(
                event_name="Resilience Test Festival",
                event_category="Festival",
                event_date="2026-10-25",
                city_location="Kolkata",
                guest_count=500,
                total_budget=200000.0
            )

            # Should not raise exception
            blueprint = generate_ai_event_blueprint(inp)
            assert blueprint is not None
            assert blueprint["used_live_ai"] is False
            assert "Demonstration" in blueprint["model_used"]


def test_plan_rescue_fallback_when_credentials_absent():
    """Verify Plan Rescue fallback advice generation."""
    with patch.dict(os.environ, {}, clear=True):
        req = PlanRescueRequest(
            event_id="e-test",
            disruption_type="Bad weather affecting outdoor event",
            disruption_details="Rainstorm approaching venue",
            additional_guests=10
        )
        event_data = {
            "name": "Lawn Gathering",
            "category": "Community Gathering",
            "city": "Bangalore",
            "venue_type": "Outdoor",
            "guest_count": 50,
            "total_budget": 50000.0,
            "currency": "INR"
        }
        budget_impact = {
            "total_cost_increase": 2000.0,
            "cut_amount_needed": 2000.0,
            "new_guest_count": 60
        }

        rec, used_ai, model = generate_plan_rescue_advice(req, event_data, budget_impact)
        assert used_ai is False
        assert len(rec.recommended_alternatives) > 0
        assert len(rec.contingency_steps) > 0


def test_sanitize_api_message_redacts_keys():
    """Verify that sensitive API key patterns are strictly redacted from messages."""
    raw_error = "Failed to authenticate with key=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q and header AIzaSy1234567890abcdefghijklmnopqrstuv"
    cleaned = sanitize_api_message(raw_error)
    assert "AIzaSy" not in cleaned
    assert "[REDACTED" in cleaned


def test_classify_gemini_error_distinguishes_503_from_invalid_key():
    """Verify that 503 is classified as temporary unavailable and NOT invalid key."""
    exc_503 = Exception("503 UNAVAILABLE: This model is currently experiencing high demand. Please try again later.")
    cat_503, msg_503 = classify_gemini_error(exc_503, model="gemini-3.8-flash")
    assert cat_503 == "TEMPORARY_UNAVAILABLE"
    assert "high demand" in msg_503.lower()

    exc_400 = Exception("API_KEY_INVALID: API key not valid. Please pass a valid API key.")
    cat_400, msg_400 = classify_gemini_error(exc_400, model="gemini-3.8-flash")
    assert cat_400 == "INVALID_KEY"
    assert "rejected" in msg_400.lower()


def test_verify_gemini_connection_503_fallback():
    """Verify that verify_gemini_connection retries 503 and falls back to secondary candidate."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # First call on primary (attempt 1) -> 503
        # Second call on primary (attempt 2 retry) -> 503
        # Third call on fallback -> success
        err_503 = Exception("503 UNAVAILABLE: high demand")
        success_resp = MagicMock()
        success_resp.text = "FESTIWISE_OK"

        mock_client.models.generate_content.side_effect = [err_503, err_503, success_resp]

        res = verify_gemini_connection(
            api_key="AIzaSyDummyKeyForTestingPurposes12345",
            model_name="gemini-3.8-flash",
            allow_fallback=True,
            max_retries=1
        )

        assert res["success"] is True
        assert res["fallback_used"] is True
        assert res["model_used"] != "gemini-3.8-flash"
        assert res["response_text"] == "FESTIWISE_OK"
        assert len(res["diagnostic_trail"]) >= 3


def test_verify_gemini_connection_invalid_key_stops_early():
    """Verify that an invalid API key halts immediately without trying other models."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        err_invalid = Exception("400 API_KEY_INVALID: bad key")
        mock_client.models.generate_content.side_effect = err_invalid

        res = verify_gemini_connection(
            api_key="AIzaSyBadKey1234567890123456789012345",
            model_name="gemini-3.8-flash",
            allow_fallback=True,
            max_retries=1
        )

        assert res["success"] is False
        assert res["error_category"] == "INVALID_KEY"
        # Should only have attempted once
        assert mock_client.models.generate_content.call_count == 1


def test_get_config_val_and_gemini_key():
    """Verify config retrieval helper behavior across env and defaults."""
    from config import get_config_val, get_gemini_api_key

    with patch.dict(os.environ, {}, clear=True):
        assert get_config_val("NON_EXISTENT_VAR", "default_val") == "default_val"
        assert get_gemini_api_key() == ""

    with patch.dict(os.environ, {"TEST_KEY": "test_val", "GEMINI_API_KEY": "test_gemini_key"}):
        assert get_config_val("TEST_KEY", "default_val") == "test_val"
        assert get_gemini_api_key() == "test_gemini_key"


