import os
from typing import Optional

class FeatureFlags:
    """Simple env-driven feature flag reader.
    Flags are enabled if the corresponding env var equals '1', 'true', or 'yes' (case-insensitive).
    """

    TRUTHY = {"1", "true", "yes", "on"}

    def __init__(self, prefix: str = "AI_TEAM_"):
        self.prefix = prefix

    def is_enabled(self, name: str, default: bool = False) -> bool:
        key = f"{self.prefix}{name}".upper()
        val: Optional[str] = os.getenv(key)
        if val is None:
            return default
        return val.strip().lower() in self.TRUTHY


