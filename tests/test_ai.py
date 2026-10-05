from unittest.mock import patch, MagicMock
from app.services import ai_service


def test_ai_disabled_when_groq_key_missing(app, client, engineer_token):
    with app.app_context():
        # Ensure key is None
        app.config["GROQ_API_KEY"] = None
        assert ai_service.is_ai_available() is False

        # Endpoint returns available=False
        res = client.get("/api/ai/status", headers={"Authorization": f"Bearer {engineer_token}"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["available"] is False

        # Endpoint returns 503 disabled message
        gen_res = client.post("/api/ai/generate-runbook", headers={
            "Authorization": f"Bearer {engineer_token}"
        }, json={"prompt": "Restart Redis"})
        assert gen_res.status_code == 503
        assert "not configured" in gen_res.get_json()["message"]


def test_ai_generate_runbook_mocked_groq(app):
    with app.app_context():
        app.config["GROQ_API_KEY"] = "gsk-mock-key-for-test"
        assert ai_service.is_ai_available() is True

        mock_groq_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"title": "Mocked Runbook", "description": "AI generated", "steps": [{"order": 1, "title": "Step 1", "instructions": "run", "expectedOutcome": "ok"}]}'
        mock_groq_response.choices = [mock_choice]

        with patch("groq.Groq") as mock_groq_class:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_groq_response
            mock_groq_class.return_value = mock_instance

            result = ai_service.generate_runbook_from_prompt("Generate test runbook")
            assert result["success"] is True
            assert result["data"]["title"] == "Mocked Runbook"
            assert len(result["data"]["steps"]) == 1

            # Ensure llama model was specified
            call_kwargs = mock_instance.chat.completions.create.call_args[1]
            assert "llama" in call_kwargs["model"].lower()
            assert call_kwargs["response_format"] == {"type": "json_object"}
