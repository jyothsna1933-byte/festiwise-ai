"""Test Gemini API integration, error handling, and demo mode fallbacks for FestiWise AI."""

import os
from unittest.mock import patch, MagicMock
from models.schemas import EventInput, PlanRescueRequest
from services.gemini_service import (
    is_gemini_available,
    generate_ai_event_blueprint,
    generate_plan_rescue_advice
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
