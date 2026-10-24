from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
    
    # Storage Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", "./audit_logs")
    
    # TinyFish API Key (Optional: fallbacks to SIMULATED if unset)
    TINYFISH_API_KEY: str = os.getenv("TINYFISH_API_KEY", "")
    TINYFISH_API_URL: str = "https://agent.tinyfish.ai/v1/automation/run"
    
    # Rules
    RULES_VERSION: str = "2.0.0"


settings = Settings()
