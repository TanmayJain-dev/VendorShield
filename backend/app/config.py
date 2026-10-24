from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
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
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vendorshield.db")

    # Storage Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", "./audit_logs")
    
    # Security & Upload Validation
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    MAX_PDF_PAGES: int = 25
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/png", "image/jpeg"]

    # Reviewer Authentication & Dev Mode
    REVIEWER_DEV_MODE: bool = True
    DEV_REVIEWER_TOKEN: str = os.getenv("DEV_REVIEWER_TOKEN", "vendorshield-dev-review-token-2026")

    # TinyFish API Key (Optional: fallbacks to SIMULATED if unset)
    TINYFISH_API_KEY: str = os.getenv("TINYFISH_API_KEY", "")
    TINYFISH_API_URL: str = "https://agent.tinyfish.ai/v1/automation/run"
    
    # Rules
    RULES_VERSION: str = "2.0.0"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if self.REVIEWER_DEV_MODE:
                raise ValueError("Insecure configuration: REVIEWER_DEV_MODE cannot be enabled in production environment.")
            if not self.DEV_REVIEWER_TOKEN or self.DEV_REVIEWER_TOKEN == "vendorshield-dev-review-token-2026":
                raise ValueError("Insecure configuration: Production mode rejects the default dev reviewer token. Configure a secure, explicit reviewer token.")
        return self

settings = Settings()
