"""ComfyUI node that sends text to the Google Gemini API and returns the response."""

import json
import os
import urllib.error
import urllib.request

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ENV_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

MODELS = [
    "gemini-3.1-flash-lite",   # default: cheapest current-gen, fast
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.8-flash",
]

# Permissive API-side filters so the model follows the text instead of refusing outright.
SAFETY_SETTINGS = [
    {"category": c, "threshold": "BLOCK_NONE"}
    for c in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]


def _read_config_key():
    if not os.path.isfile(CONFIG_PATH):
        return ""
    try:
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            return str(json.load(f).get("api_key", "")).strip()
    except (OSError, ValueError, AttributeError) as e:
        raise RuntimeError(f"Could not read {CONFIG_PATH}: {e}") from e


def _get_api_key():
    # Read on every call so edits to config.json apply without restarting ComfyUI.
    key = _read_config_key()
    if key:
        return key
    for name in ENV_KEYS:
        key = os.environ.get(name, "").strip()
        if key:
            return key
    raise RuntimeError(
        f"Gemini API key not found. Add it to {CONFIG_PATH} "
        "(see config.example.json) or set the GEMINI_API_KEY environment variable."
    )


def _call_gemini(model, text, temperature, timeout):
    body = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": temperature},
        "safetySettings": SAFETY_SETTINGS,
    }
    req = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": _get_api_key()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach Gemini API: {e.reason}") from e

    feedback = data.get("promptFeedback", {})
    if feedback.get("blockReason"):
        raise RuntimeError(f"Gemini blocked the request: {feedback['blockReason']}")

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    result = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not result:
        reason = candidates[0].get("finishReason", "unknown")
        raise RuntimeError(f"Gemini returned an empty response (finishReason: {reason})")
    return result


class GeminiPromptSanitizer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Full message sent to Gemini: your instruction followed by the prompt.",
                }),
                "model": (MODELS, {
                    "default": MODELS[0],
                    "tooltip": "Gemini model. Flash-Lite models are the fastest and cheapest.",
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 2.0, "step": 0.05,
                    "tooltip": "0 gives the most consistent output; higher values add variation.",
                }),
                "timeout_seconds": ("INT", {
                    "default": 60, "min": 5, "max": 600,
                    "tooltip": "Seconds to wait for the Gemini API before failing.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    OUTPUT_TOOLTIPS = ("Gemini's text response.",)
    FUNCTION = "run"
    CATEGORY = "text/LLM"
    DESCRIPTION = (
        "Sends text to the Google Gemini API and returns the response as a STRING. "
        "Reads the API key from config.json in the node folder, or from the GEMINI_API_KEY "
        "(or GOOGLE_API_KEY) environment variable."
    )

    def run(self, text, model, temperature=0.0, timeout_seconds=60):
        if not text.strip():
            return ("",)
        return (_call_gemini(model, text, temperature, timeout_seconds),)


NODE_CLASS_MAPPINGS = {"GeminiPromptSanitizer": GeminiPromptSanitizer}
NODE_DISPLAY_NAME_MAPPINGS = {"GeminiPromptSanitizer": "Gemini Prompt Rewriter"}
