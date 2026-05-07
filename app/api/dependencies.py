"""FastAPI dependency providers."""

from functools import lru_cache
from app.services.processor import ClaimsProcessor


@lru_cache(maxsize=1)
def get_claims_processor() -> ClaimsProcessor:
    """Singleton processor (services inside are stateless)."""
    return ClaimsProcessor()