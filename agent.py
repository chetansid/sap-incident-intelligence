from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_incident(error_message: str) -> dict:
    prompt = f"""
    You are an expert SAP BASIS administrator with 20 years of experience.
    Analyze this SAP error message and respond ONLY with a JSON object.
    No preamble, no explanation, just the JSON.

    Error message: {error_message}

    Respond with exactly this structure:
    {{
        "sap_module": "which SAP module this relates to (BASIS, FI, MM, SD, etc)",
        "root_cause": "what is causing this error in plain English",
        "impact": "what business operations are affected by this error",
        "resolution_steps": "numbered step by step fix in plain English",
        "severity": "LOW, MEDIUM, HIGH, or CRITICAL"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw = response.choices[0].message.content.strip()
        
        # Clean up if model wraps in markdown
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        # AI Model did not return valid JSON
        raise ValueError(f"AI analysis did not return valid JSON: {raw}")
    except Exception as e:
        # OpenAI API failed
        raise ValueError(f"AI analysis failed: {str(e)}")