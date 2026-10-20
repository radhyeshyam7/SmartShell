import time
import logging
from typing import Optional
from google import genai
from backend.app.config import settings

class GeminiClient:
    """Wrapper around official google-genai SDK with retry & model failover logic"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def update_key(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_content(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("Gemini API key is not configured. Please set GEMINI_API_KEY in Settings or .env.")

        models_to_try = [self.model_name]
        for fallback in ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-3.8-flash', 'gemini-flash-latest']:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_exception = None
        for model_id in models_to_try:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model_id,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip()
                    return ""
                except Exception as e:
                    last_exception = e
                    err_str = str(e)
                    if any(code in err_str for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                        logging.warning(f"Model {model_id} transient error ({err_str}). Retrying...")
                        time.sleep(1)
                        continue
                    else:
                        break

        if last_exception:
            raise last_exception
        return ""

gemini_client = GeminiClient()
