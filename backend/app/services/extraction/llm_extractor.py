import abc
import base64
import json
import logging
import re
from typing import Optional, Dict, Any, List
import httpx
from pydantic import BaseModel, Field

from ...config import settings

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert invoice data extraction assistant for an accounts payable audit system.
Analyze the provided invoice document and extract all fields into a single, valid JSON object matching this schema.

Rules:
1. Extract exact values from the document. Do not invent or fabricate data.
2. If a field is not present or cannot be found, use null.
3. For bank account number: Return ONLY the last 4 digits (e.g., "1234"). Do not return the full account number.
4. Clean and normalize dates to ISO format YYYY-MM-DD where possible.
5. Extract numeric values (amounts, rates) as pure numbers without currency symbols or commas.
6. Return ONLY the JSON object. Do not include markdown code fences or conversational text.

Schema:
{
  "supplier_name": "Trade name of vendor / seller",
  "legal_name": "Full legal registered entity name if different",
  "supplier_gstin": "15-character GSTIN of supplier",
  "buyer_name": "Name of the customer / bill-to entity",
  "buyer_gstin": "15-character GSTIN of customer / bill-to entity",
  "invoice_number": "Invoice / bill number",
  "invoice_date": "YYYY-MM-DD",
  "place_of_supply": "State name or 2-digit state code",
  "taxable_amount": 0.0,
  "cgst": 0.0,
  "sgst": 0.0,
  "igst": 0.0,
  "cess": 0.0,
  "round_off": 0.0,
  "discount_amount": 0.0,
  "total_amount": 0.0,
  "currency": "INR",
  "bank_name": "Name of bank",
  "ifsc_code": "11-character IFSC",
  "bank_account_last4": "Last 4 digits only",
  "irn": "64-character e-invoice IRN if printed",
  "line_items": [
    {
      "description": "Item description",
      "hsn_code": "HSN/SAC",
      "quantity": 1.0,
      "unit_price": 0.0,
      "taxable_value": 0.0,
      "tax_rate": 0.0,
      "total": 0.0
    }
  ]
}
"""

class LlmExtractedLineItem(BaseModel):
    description: str
    hsn_code: Optional[str] = None
    quantity: float = 1.0
    unit_price: float = 0.0
    taxable_value: float = 0.0
    tax_rate: Optional[float] = None
    total: float = 0.0

class LlmExtractedInvoice(BaseModel):
    supplier_name: Optional[str] = None
    legal_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    place_of_supply: Optional[str] = None
    taxable_amount: Optional[float] = None
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    cess: Optional[float] = None
    round_off: Optional[float] = None
    discount_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_account_last4: Optional[str] = None
    irn: Optional[str] = None
    line_items: List[LlmExtractedLineItem] = Field(default_factory=list)

class ExtractionProvider(abc.ABC):
    @abc.abstractmethod
    async def extract(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Extracts structured invoice data from file bytes."""
        pass

class NoneExtractor(ExtractionProvider):
    async def extract(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        return {}

class GeminiExtractor(ExtractionProvider):
    def __init__(self, api_key: str, model: str = ""):
        self.api_key = api_key
        self.model = model or "gemini-1.5-flash"
        self.transport: Optional[httpx.AsyncBaseTransport] = None  # for testing/mocking

    async def extract(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        
        b64_content = base64.b64encode(file_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64_content}},
                        {"text": EXTRACTION_SYSTEM_PROMPT}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=35.0, transport=self.transport) as client:
            for attempt in range(2):
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                        return {}
                    
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return {}
                    
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        return {}
                    
                    text_out = parts[0].get("text", "")
                    parsed = self._parse_and_validate(text_out)
                    if parsed:
                        return parsed
                except Exception as e:
                    logger.warning(f"Gemini extraction attempt {attempt + 1} failed: {e}")
                    if attempt == 1:
                        return {}
        return {}

    def _parse_and_validate(self, text_out: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = text_out.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            raw_dict = json.loads(cleaned.strip())
            validated = LlmExtractedInvoice(**raw_dict)
            return validated.model_dump(exclude_none=True)
        except Exception as e:
            logger.warning(f"Failed to validate LLM JSON response: {e}")
            return None

class AnthropicExtractor(ExtractionProvider):
    def __init__(self, api_key: str, model: str = ""):
        self.api_key = api_key
        self.model = model or "claude-3-5-sonnet-20241022"
        self.transport: Optional[httpx.AsyncBaseTransport] = None

    async def extract(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        b64_content = base64.b64encode(file_bytes).decode("utf-8")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Format content block according to mime_type
        if mime_type == "application/pdf":
            content_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64_content
                }
            }
        else:
            content_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": b64_content
                }
            }

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {"type": "text", "text": EXTRACTION_SYSTEM_PROMPT}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=35.0, transport=self.transport) as client:
            for attempt in range(2):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        logger.warning(f"Anthropic API returned status {resp.status_code}: {resp.text}")
                        return {}
                    
                    data = resp.json()
                    content_blocks = data.get("content", [])
                    if not content_blocks:
                        return {}
                    
                    text_out = content_blocks[0].get("text", "")
                    parsed = self._parse_and_validate(text_out)
                    if parsed:
                        return parsed
                except Exception as e:
                    logger.warning(f"Anthropic extraction attempt {attempt + 1} failed: {e}")
                    if attempt == 1:
                        return {}
        return {}

    def _parse_and_validate(self, text_out: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = text_out.strip()
            # Extract JSON substring if wrapped in markdown
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                cleaned = match.group(0)
            raw_dict = json.loads(cleaned)
            validated = LlmExtractedInvoice(**raw_dict)
            return validated.model_dump(exclude_none=True)
        except Exception as e:
            logger.warning(f"Failed to validate Anthropic JSON response: {e}")
            return None

def get_llm_extractor() -> ExtractionProvider:
    provider = (settings.LLM_PROVIDER or "none").strip().lower()
    if provider == "gemini":
        return GeminiExtractor(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    elif provider == "anthropic":
        return AnthropicExtractor(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    return NoneExtractor()
