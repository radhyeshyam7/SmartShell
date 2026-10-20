import re
from backend.app.config import settings

SECRET_PATTERNS = [
    re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'),  # Google API Key
    re.compile(r'sk-[A-Za-z0-9]{32,}'),      # OpenAI key style
    re.compile(r'ghp_[A-Za-z0-9]{36}'),       # GitHub token
    re.compile(r'(?i)(password|secret|token|api_key)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'),
]

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    
    sanitized = text
    # Redact configured GEMINI_API_KEY if present
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 5:
        sanitized = sanitized.replace(settings.GEMINI_API_KEY, "[REDACTED_API_KEY]")
        
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(r'\1: [REDACTED]', sanitized) if 'password' in pattern.pattern else pattern.sub('[REDACTED_SECRET]', sanitized)
        
    return sanitized
