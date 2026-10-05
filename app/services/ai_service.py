import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def is_ai_available() -> bool:
    """Check if Groq API is configured and ready."""
    try:
        api_key = current_app.config.get("GROQ_API_KEY")
        return bool(api_key and str(api_key).strip())
    except Exception:
        return False


def get_groq_client():
    """Instantiate Groq client only if GROQ_API_KEY is configured."""
    if not is_ai_available():
        return None
    try:
        from groq import Groq
        api_key = current_app.config.get("GROQ_API_KEY")
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None


def generate_runbook_from_prompt(prompt: str) -> dict:
    """Generate a structured runbook specification using Groq Llama model."""
    if not is_ai_available():
        return {
            "success": False,
            "message": "Groq AI is disabled because GROQ_API_KEY is not configured in .env."
        }

    client = get_groq_client()
    if not client:
        return {
            "success": False,
            "message": "Unable to initialize Groq client."
        }

    model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    system_prompt = (
        "You are an expert Site Reliability Engineer (SRE) and DevOps Automation Architect. "
        "Your task is to generate complete, high-quality, production-ready operational runbooks. "
        "You must respond ONLY with a valid JSON object matching this exact schema:\n"
        "{\n"
        '  "title": "string (concise and descriptive)",\n'
        '  "description": "string (context, purpose, and prerequisites)",\n'
        '  "steps": [\n'
        "    {\n"
        '      "order": 1,\n'
        '      "title": "string (action-oriented step title)",\n'
        '      "instructions": "string (exact terminal commands, scripts, or operational instructions)",\n'
        '      "expectedOutcome": "string (precise expected output, status code, or log message)"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Ensure steps are logical, sequential, safe, and include verification commands."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an operational runbook for the following incident/procedure:\n\n{prompt.strip()}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2500
        )
        content = response.choices[0].message.content
        data = json.loads(content)

        # Validate structure
        if "title" not in data or "steps" not in data or not isinstance(data["steps"], list):
            return {
                "success": False,
                "message": "AI generated an invalid runbook format. Please retry."
            }

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        logger.error(f"Groq API error during runbook generation: {e}")
        return {
            "success": False,
            "message": f"Groq AI error: {str(e)}"
        }


def troubleshoot_step(step_title: str, step_instructions: str, expected_outcome: str, user_observation: str) -> dict:
    """Provide AI troubleshooting assistance during runbook execution."""
    if not is_ai_available():
        return {
            "success": False,
            "message": "Groq AI is disabled because GROQ_API_KEY is not configured."
        }

    client = get_groq_client()
    if not client:
        return {
            "success": False,
            "message": "Unable to initialize Groq client."
        }

    model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    system_prompt = (
        "You are an on-call SRE incident assistant. An operator is executing a runbook and has run into an issue or unexpected outcome. "
        "Analyze the step details and the operator's observation. "
        "Provide a concise, direct troubleshooting plan:\n"
        "1. Likely root cause(s)\n"
        "2. Immediate diagnostic commands to inspect system state\n"
        "3. Safe remediation / bypass steps to resume operation."
    )

    user_content = (
        f"RUNBOOK STEP TITLE: {step_title}\n"
        f"INSTRUCTIONS EXECUTED:\n{step_instructions}\n"
        f"EXPECTED OUTCOME:\n{expected_outcome}\n"
        f"OPERATOR OBSERVATION / ERROR OUTPUT:\n{user_observation}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        advice = response.choices[0].message.content
        return {
            "success": True,
            "advice": advice
        }
    except Exception as e:
        logger.error(f"Groq AI error during step troubleshooting: {e}")
        return {
            "success": False,
            "message": f"Groq AI error: {str(e)}"
        }
