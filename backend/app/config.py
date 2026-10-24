import json
import os
from typing import List, Union, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "VendorShield AI"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vendorshield.vercel.app"
    ]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return list(v)
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vendorshield.db")

    # Storage Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", "./audit_logs")
    
    # Security & Upload Validation
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    MAX_PDF_PAGES: int = 25
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/png", "image/jpeg"]

    # Authentication & Authorization (Phase D)
    USERS_JSON: str = os.getenv("USERS_JSON", "")
    AUTH_DISABLED: bool = False
    REVIEWER_DEV_MODE: bool = True
    DEV_REVIEWER_TOKEN: str = os.getenv("DEV_REVIEWER_TOKEN", "vendorshield-dev-review-token-2026")

    # Demo Mode & Seeding Isolation
    DEMO_MODE: bool = False
    SEED_DEMO_DATA: bool = False

    # TinyFish Web Research API
    TINYFISH_API_KEY: str = os.getenv("TINYFISH_API_KEY", "")
    TINYFISH_API_URL: str = os.getenv("TINYFISH_API_URL", "https://agent.tinyfish.ai/v1/automation/run")

    # Experimental Forensics (Hops 2-4: ZaubaCorp, Google Maps, NCLT)
    ENABLE_EXPERIMENTAL_FORENSICS: bool = False

    # Extraction Pipeline (Phase B: QR + Text + LLM)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")  # gemini | anthropic | none
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # Registry Providers (Phase C: Manual, HttpKyc, TinyFish, Demo)
    GSTIN_PROVIDERS: str = os.getenv("GSTIN_PROVIDERS", "manual")  # comma-separated provider order
    GSTIN_API_URL_TEMPLATE: str = os.getenv("GSTIN_API_URL_TEMPLATE", "")
    GSTIN_API_AUTH_HEADER: str = os.getenv("GSTIN_API_AUTH_HEADER", "")
    GSTIN_API_AUTH_VALUE: str = os.getenv("GSTIN_API_AUTH_VALUE", "")
    GSTIN_API_FIELD_MAP: str = os.getenv("GSTIN_API_FIELD_MAP", "{}")

    # Own Registered Entity GSTINs (for Buyer GSTIN matching)
    BUYER_GSTINS: Union[List[str], str] = []

    @field_validator("BUYER_GSTINS")
    @classmethod
    def assemble_buyer_gstins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip().upper() for i in v.split(",") if i.strip()]
        return [str(i).strip().upper() for i in v]

    # E-Invoice Public Key (PEM formatted string or path, optional)
    IRP_PUBLIC_KEY_PEM: str = os.getenv("IRP_PUBLIC_KEY_PEM", "")
    
    # Rules
    RULES_VERSION: str = "2.0.0"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if self.REVIEWER_DEV_MODE:
                raise ValueError("Insecure configuration: REVIEWER_DEV_MODE cannot be enabled in production environment.")
            if not self.DEV_REVIEWER_TOKEN or self.DEV_REVIEWER_TOKEN == "vendorshield-dev-review-token-2026":
                raise ValueError("Insecure configuration: Production mode rejects the default dev reviewer token. Configure a secure, explicit reviewer token.")
            if self.AUTH_DISABLED:
                raise ValueError("Insecure configuration: AUTH_DISABLED cannot be true in production environment.")
        return self

settings = Settings()
