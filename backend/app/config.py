from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "VendorShield AI"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vendorshield.vercel.app"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    # Storage Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", "./audit_logs")
    
    # TinyFish API Key (Optional: fallbacks to SIMULATED if unset)
    TINYFISH_API_KEY: str = os.getenv("TINYFISH_API_KEY", "")
    TINYFISH_API_URL: str = "https://agent.tinyfish.ai/v1/automation/run"
    
    # Rules
    RULES_VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

