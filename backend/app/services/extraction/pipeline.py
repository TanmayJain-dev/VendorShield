import hashlib
import logging
from typing import Optional
from ...schemas.invoice import InvoiceClaim
from .qr_einvoice import extract_qr_einvoice
from .text_layer import extract_text_from_pdf, extract_text_layer
from .llm_extractor import get_llm_extractor
from .merge import merge_extractions

logger = logging.getLogger(__name__)

async def extract_invoice(
    file_bytes: bytes,
    filename: str = "invoice.pdf",
    mime_type: Optional[str] = None
) -> InvoiceClaim:
    """
    Unified layered extraction pipeline:
    1. QR code decode & e-invoice JWT claims (highest confidence)
    2. PyMuPDF text & regex extraction layer
    3. Multimodal LLM extraction (Gemini / Anthropic if configured)
    4. Deterministic merge with precedence QR > LLM > REGEX and conflict detection.
    """
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    lower_fn = filename.lower()
    is_pdf = lower_fn.endswith(".pdf") or (mime_type == "application/pdf")
    effective_mime = mime_type or ("application/pdf" if is_pdf else "image/jpeg")

    # Layer 1: E-Invoice QR Code
    qr_result = extract_qr_einvoice(file_bytes, is_pdf=is_pdf)

    # Layer 2: Text & Regex Layer
    if is_pdf:
        text, is_scanned, ocr_msg, errors = extract_text_from_pdf(file_bytes)
        text_result = extract_text_layer(text, is_scanned=is_scanned, ocr_msg=ocr_msg)
        if errors:
            text_result.parsing_errors.extend(errors)
    else:
        # For pure image uploads, text layer has no native text
        text_result = extract_text_layer(
            "",
            is_scanned=True,
            ocr_msg="Image upload without native PDF text layer."
        )

    # Layer 3: Multimodal LLM Extractor (if enabled)
    llm_fields = {}
    try:
        llm_extractor = get_llm_extractor()
        llm_fields = await llm_extractor.extract(file_bytes, effective_mime)
    except Exception as e:
        logger.warning(f"LLM extraction encountered an error: {e}")

    # Layer 4: Merge & Validate
    claim = merge_extractions(
        qr_result=qr_result,
        text_result=text_result,
        llm_fields=llm_fields,
        raw_file_bytes=file_bytes,
        file_sha256=file_sha256
    )

    return claim
