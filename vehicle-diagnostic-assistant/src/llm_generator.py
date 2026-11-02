"""
LLM Generator Module
Uses an LLM API to generate diagnostic explanations
based on retrieved context and vehicle data.

Supported providers: "groq" (free tier), "openai", "anthropic"
"""

import json
import re
from typing import Dict, Optional

import config

# Try importing the client libraries. Groq uses the OpenAI-compatible
# endpoint, so it needs the "openai" package and nothing extra.
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
REQUEST_TIMEOUT = 30  # seconds

SEVERITY_ORDER = ["NORMAL", "WARNING", "CRITICAL", "IMMEDIATE"]


def _api_key_for(provider: str) -> Optional[str]:
    return {
        "openai": config.OPENAI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "groq": config.GROQ_API_KEY,
    }.get(provider)


def _is_placeholder(key: Optional[str]) -> bool:
    """True when the key is missing or still the example text."""
    return (not key) or key.strip().lower().startswith("your-")


def create_explainer():
    """
    Build a DiagnosticExplainer from config, or return None when the
    provider has no real API key (the app then shows retrieval only).
    """
    provider = config.LLM_PROVIDER
    if _is_placeholder(_api_key_for(provider)):
        print(f"⚠️ No API key set for provider '{provider}' - AI explanations are off")
        return None
    try:
        return DiagnosticExplainer(provider)
    except Exception as e:
        print(f"⚠️ Could not initialize LLM: {e}")
        return None


class DiagnosticExplainer:
    """
    Generates plain-language explanations using an LLM.
    Ensures responses are grounded in the provided context.
    """

    def __init__(self, provider: str = None):
        """
        Initialize the LLM client.

        Args:
            provider: "groq", "openai" or "anthropic" (defaults to config)
        """
        self.provider = (provider or config.LLM_PROVIDER).lower()
        self.client = None

        if self.provider in ("openai", "groq"):
            if not OPENAI_AVAILABLE:
                raise ImportError("The openai library is not installed. Run: python -m pip install openai")
            kwargs = {"api_key": _api_key_for(self.provider), "timeout": REQUEST_TIMEOUT}
            if self.provider == "groq":
                kwargs["base_url"] = GROQ_BASE_URL
            self.client = OpenAI(**kwargs)

        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("The anthropic library is not installed. Run: python -m pip install anthropic")
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=REQUEST_TIMEOUT)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        print(f"🤖 Initialized {self.provider} client with model: {config.LLM_MODEL}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_explanation(
        self,
        query: str,
        context: str,
        safety_report: Dict = None
    ) -> Dict:
        """
        Generate a diagnostic explanation.

        Returns a dict with: explanation, severity, confidence,
        checklist and estimated_urgency.
        """
        prompt = self._build_prompt(query, context, safety_report)

        if self.provider in ("openai", "groq"):
            response = self._generate_openai_compatible(prompt)
        else:
            response = self._generate_anthropic(prompt)

        result = self._parse_response(response)
        return self._apply_safety_floor(result, safety_report)

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------
    def _build_prompt(self, query: str, context: str, safety_report: Dict = None) -> str:
        prompt_parts = []

        prompt_parts.append("""You are an expert vehicle diagnostic assistant. Your role is to provide clear, accurate explanations based ONLY on the provided context.

IMPORTANT RULES:
1. Base your response ONLY on the provided technical information
2. Do NOT make up or guess information
3. If the context doesn't contain the answer, say so
4. Provide practical, actionable advice
5. Use simple language that non-mechanics can understand
6. Reply with the JSON object only, no text before or after it

Your response must be in the following JSON format:
{
    "explanation": "Clear explanation of the issue in 2-3 short paragraphs",
    "severity": "NORMAL/WARNING/CRITICAL/IMMEDIATE",
    "confidence": "HIGH/MEDIUM/LOW based on available information",
    "checklist": [
        "First inspection/action item",
        "Second inspection/action item",
        "Third inspection/action item"
    ],
    "estimated_urgency": "Timeframe for addressing the issue"
}
""")

        if safety_report:
            prompt_parts.append("\n=== SAFETY ANALYSIS ===")
            prompt_parts.append(f"Severity: {safety_report.get('severity', 'UNKNOWN')}")
            if safety_report.get('alerts'):
                prompt_parts.append("Alerts:")
                for alert in safety_report['alerts']:
                    prompt_parts.append(f"  - {alert}")

        prompt_parts.append("\n=== TECHNICAL INFORMATION ===")
        prompt_parts.append(context)

        prompt_parts.append("\n=== USER QUESTION ===")
        prompt_parts.append(query)

        prompt_parts.append("\n=== YOUR RESPONSE ===")
        prompt_parts.append("Provide your response in the JSON format specified above:")

        return "\n".join(prompt_parts)

    # ------------------------------------------------------------------
    # Provider calls
    # ------------------------------------------------------------------
    def _generate_openai_compatible(self, prompt: str) -> str:
        """OpenAI and Groq share the same chat-completions interface."""
        messages = [
            {"role": "system", "content": "You are an expert vehicle diagnostic assistant. Reply with JSON only."},
            {"role": "user", "content": prompt},
        ]
        base = dict(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        try:
            try:
                # JSON mode makes the reply far more likely to parse
                response = self.client.chat.completions.create(
                    response_format={"type": "json_object"}, **base
                )
            except Exception as json_mode_error:
                print(f"⚠️ JSON mode failed ({json_mode_error}); retrying without it")
                response = self.client.chat.completions.create(**base)
            return response.choices[0].message.content or ""

        except Exception as e:
            print(f"❌ {self.provider} API error: {e}")
            return self._generate_fallback_response(str(e))

    def _generate_anthropic(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=config.LLM_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        except Exception as e:
            print(f"❌ Anthropic API error: {e}")
            return self._generate_fallback_response(str(e))

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_json(text: str) -> Dict:
        """Pull a JSON object out of a reply, with or without code fences."""
        text = (text or "").strip()
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                return json.loads(text[start:end + 1])
            raise

    def _parse_response(self, response: str) -> Dict:
        """Turn the raw reply into a clean, fully populated dictionary."""
        try:
            parsed = self._extract_json(response)
            if not isinstance(parsed, dict):
                raise ValueError("Reply was not a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Failed to parse JSON response: {e}")
            return self._salvage_text(response)

        # Normalise every field so the web page can rely on the types
        severity = str(parsed.get("severity", "")).strip().upper()
        if severity not in SEVERITY_ORDER:
            severity = "UNKNOWN"

        checklist = parsed.get("checklist")
        if isinstance(checklist, str):
            checklist = [checklist]
        if not isinstance(checklist, list) or not checklist:
            checklist = ["Consult a professional mechanic for detailed diagnosis"]

        return {
            "explanation": str(parsed.get("explanation") or "No explanation available."),
            "severity": severity,
            "confidence": str(parsed.get("confidence") or "LOW").upper(),
            "checklist": [str(item) for item in checklist],
            "estimated_urgency": str(parsed.get("estimated_urgency") or "Unknown"),
        }

    @staticmethod
    def _salvage_text(response: str) -> Dict:
        """When JSON is broken or cut off, recover the explanation if we can."""
        text = (response or "").strip()
        match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)', text, re.DOTALL)
        if match:
            try:
                text = json.loads('"' + match.group(1) + '"')
            except json.JSONDecodeError:
                text = match.group(1).replace("\\n", "\n").replace('\\"', '"')
        return {
            "explanation": text or "No explanation available.",
            "severity": "UNKNOWN",
            "confidence": "LOW",
            "checklist": ["Consult a professional mechanic for detailed diagnosis"],
            "estimated_urgency": "Unknown",
        }

    @staticmethod
    def _apply_safety_floor(result: Dict, safety_report: Optional[Dict]) -> Dict:
        """
        The rule-based safety checker is the authority on severity.
        If the LLM reports a lower level (or none), raise it to the rule level.
        """
        if not safety_report:
            return result
        rule = str(safety_report.get("severity", "")).strip().upper()
        if rule not in SEVERITY_ORDER:
            return result
        llm = result.get("severity", "UNKNOWN")
        if llm not in SEVERITY_ORDER or SEVERITY_ORDER.index(rule) > SEVERITY_ORDER.index(llm):
            result["severity"] = rule
        return result

    def _generate_fallback_response(self, reason: str = "") -> str:
        """JSON string returned when the API call fails."""
        explanation = ("Unable to generate an AI explanation right now. "
                       "Please read the retrieved technical documents or consult a professional mechanic.")
        if reason:
            explanation += f" (Reason: {reason[:200]})"
        return json.dumps({
            "explanation": explanation,
            "severity": "UNKNOWN",
            "confidence": "LOW",
            "checklist": [
                "Review the retrieved technical documentation",
                "Check dashboard warning lights",
                "Consult a certified mechanic if the issue persists",
            ],
            "estimated_urgency": "Schedule inspection if symptoms worsen",
        })

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def format_for_display(self, result: Dict) -> str:
        """Format the result for terminal display."""
        output = []

        severity_emoji = {
            'NORMAL': '✅',
            'WARNING': '⚠️',
            'CRITICAL': '🔴',
            'IMMEDIATE': '🚨',
            'UNKNOWN': '❓'
        }

        emoji = severity_emoji.get(result.get('severity', 'UNKNOWN'), '❓')
        output.append(f"{emoji} **Severity: {result.get('severity', 'UNKNOWN')}**")
        output.append(f"🎯 Confidence: {result.get('confidence', 'UNKNOWN')}")
        output.append("")

        output.append("📝 **Explanation:**")
        output.append(result.get('explanation', 'No explanation available'))
        output.append("")

        output.append("🔧 **Inspection Checklist:**")
        for i, item in enumerate(result.get('checklist', []), 1):
            output.append(f"{i}. {item}")
        output.append("")

        if 'estimated_urgency' in result:
            output.append(f"⏰ **Timeframe:** {result['estimated_urgency']}")

        return "\n".join(output)


def main():
    """Demonstration of LLM explanation generation."""
    print("🤖 LLM Explainer - Demo\n")

    explainer = create_explainer()
    if explainer is None:
        print("💡 Add your API key to the .env file (see .env.example), then run again")
        return

    try:
        query = "My engine temperature is reading 115°C and I'm getting a P0301 code. What should I do?"

        context = """
=== CURRENT VEHICLE STATUS ===
RPM: 2800 rpm
Speed: 65 km/h
Coolant Temperature: 115 °C
Engine Load: 55 %
Throttle Position: 40 %

=== DIAGNOSTIC TROUBLE CODES ===
P0301: Cylinder 1 Misfire Detected

=== RELEVANT TECHNICAL INFORMATION ===

[Source 1: engine_overheating.txt]
Engine overheating is a serious condition that requires immediate attention. If temperature exceeds 120°C, pull over immediately. Common causes include low coolant, faulty thermostat, or damaged water pump.

[Source 2: dtc_p0301_misfire.txt]
DTC P0301 indicates a misfire in cylinder 1. This is a CRITICAL issue that requires service within 1-2 days. Common causes include faulty spark plugs or ignition coils.
"""

        safety_report = {
            'severity': 'CRITICAL',
            'alerts': [
                'High coolant temperature detected (115°C)',
                'Cylinder misfire code P0301 present'
            ]
        }

        print("🔄 Generating explanation...")
        result = explainer.generate_explanation(query, context, safety_report)

        print("\n" + "=" * 60)
        print(explainer.format_for_display(result))
        print("=" * 60)
        print("\n✅ LLM explanation demo completed!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
