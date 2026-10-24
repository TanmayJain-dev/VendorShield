import base64
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import cv2

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # Fallback

from ...config import settings

logger = logging.getLogger(__name__)

@dataclass
class QrExtractionResult:
    found: bool = False
    payload_raw: Optional[str] = None
    is_jwt: bool = False
    qr_signature_status: str = "NONE"  # NONE, UNVERIFIED, VERIFIED, INVALID
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    raw_claims: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

def _b64url_decode(s: str) -> bytes:
    """Decode base64url string with padding."""
    rem = len(s) % 4
    if rem > 0:
        s += "=" * (4 - rem)
    return base64.urlsafe_b64decode(s.encode("utf-8"))

def _decode_jwt_payload_lenient(jwt_str: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Decodes header and payload of a JWT without verifying the cryptographic signature.
    Returns (payload_dict, signature_status).
    """
    parts = jwt_str.strip().split(".")
    if len(parts) != 3:
        return None, "NONE"
    
    header_b64, payload_b64, signature_b64 = parts
    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload_obj = json.loads(payload_bytes.decode("utf-8", errors="replace"))
        
        # Check signature if public key is configured
        sig_status = "UNVERIFIED"
        if settings.IRP_PUBLIC_KEY_PEM:
            try:
                # Optional cryptographic signature verification
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.primitives import hashes
                
                pub_key = serialization.load_pem_public_key(settings.IRP_PUBLIC_KEY_PEM.encode("utf-8"))
                sig_bytes = _b64url_decode(signature_b64)
                message = f"{header_b64}.{payload_b64}".encode("utf-8")
                pub_key.verify(sig_bytes, message, padding.PKCS1v15(), hashes.SHA256())
                sig_status = "VERIFIED"
            except Exception as e:
                logger.warning(f"IRP QR signature verification failed: {e}")
                sig_status = "INVALID"
        
        return payload_obj, sig_status
    except Exception as e:
        logger.warning(f"Error decoding JWT QR payload: {e}")
        return None, "NONE"

def _map_einvoice_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Leniently maps e-invoice claims (which may be inside `data` claim string or top-level)
    to standard extracted fields.
    """
    inner = claims
    if "data" in claims and isinstance(claims["data"], str):
        try:
            inner = json.loads(claims["data"])
        except Exception:
            pass
    elif "data" in claims and isinstance(claims["data"], dict):
        inner = claims["data"]

    # Normalize key lookup
    normalized_keys = {k.lower().replace("_", ""): v for k, v in inner.items()}
    
    fields = {}

    # Supplier GSTIN
    for k in ["sellergstin", "suppliergstin", "seller", "supplier"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["supplier_gstin"] = str(normalized_keys[k]).strip().upper()
            break

    # Buyer GSTIN
    for k in ["buyergstin", "buyer", "customergstin"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["buyer_gstin"] = str(normalized_keys[k]).strip().upper()
            break

    # Invoice / Doc Number
    for k in ["docno", "invoiceno", "docnum", "invno", "number"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["invoice_number"] = str(normalized_keys[k]).strip()
            break

    # Invoice / Doc Date
    for k in ["docdt", "invoicedate", "docdate", "date"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["invoice_date"] = str(normalized_keys[k]).strip()
            break

    # Total Invoice Value
    for k in ["totinvval", "totalval", "totalamount", "invval", "total"]:
        if k in normalized_keys and normalized_keys[k] is not None:
            try:
                fields["total_amount"] = float(str(normalized_keys[k]).replace(",", ""))
                break
            except ValueError:
                pass

    # IRN
    for k in ["irn", "irnno"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["irn"] = str(normalized_keys[k]).strip()
            break

    # Item Count
    for k in ["itemcnt", "itemcount"]:
        if k in normalized_keys and normalized_keys[k] is not None:
            try:
                fields["item_count"] = int(normalized_keys[k])
                break
            except ValueError:
                pass

    # Main HSN
    for k in ["mainhsncode", "mainhsn", "hsncode"]:
        if k in normalized_keys and normalized_keys[k]:
            fields["main_hsn"] = str(normalized_keys[k]).strip()
            break

    return fields

def extract_qr_from_image(image_cv: np.ndarray) -> List[str]:
    """Detects and decodes all QR codes in an OpenCV image."""
    detector = cv2.QRCodeDetector()
    results = []
    
    # Try detectAndDecodeMulti first
    try:
        retval, decoded_info, points, _ = detector.detectAndDecodeMulti(image_cv)
        if retval and decoded_info:
            for text in decoded_info:
                if text and text.strip():
                    results.append(text.strip())
    except Exception as e:
        logger.debug(f"detectAndDecodeMulti failed: {e}")
        
    # If nothing found, try single detectAndDecode
    if not results:
        try:
            val, pts, _ = detector.detectAndDecode(image_cv)
            if val and val.strip():
                results.append(val.strip())
        except Exception as e:
            logger.debug(f"detectAndDecode failed: {e}")
            
    return results

def extract_qr_einvoice(file_bytes: bytes, is_pdf: bool = True) -> QrExtractionResult:
    """
    Renders PDF pages (or loads image) and extracts e-invoice QR code claims.
    """
    qr_strings: List[str] = []

    if is_pdf:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            max_pages = min(len(doc), 5)
            for page_idx in range(max_pages):
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=200)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                found = extract_qr_from_image(img)
                qr_strings.extend(found)
                if qr_strings:
                    break
            doc.close()
        except Exception as e:
            logger.warning(f"Error rendering PDF for QR extraction: {e}")
            return QrExtractionResult(errors=[f"PDF QR render error: {str(e)}"])
    else:
        try:
            np_arr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is not None:
                qr_strings = extract_qr_from_image(img)
        except Exception as e:
            logger.warning(f"Error reading image for QR extraction: {e}")
            return QrExtractionResult(errors=[f"Image QR decode error: {str(e)}"])

    if not qr_strings:
        return QrExtractionResult(found=False)

    # Process first valid QR string
    for raw in qr_strings:
        # Check if JWT
        parts = raw.split(".")
        if len(parts) == 3:
            payload, sig_status = _decode_jwt_payload_lenient(raw)
            if payload:
                extracted = _map_einvoice_claims(payload)
                return QrExtractionResult(
                    found=True,
                    payload_raw=raw,
                    is_jwt=True,
                    qr_signature_status=sig_status,
                    extracted_fields=extracted,
                    raw_claims=payload
                )
        
        # Check if raw JSON
        if raw.startswith("{") and raw.endswith("}"):
            try:
                parsed_json = json.loads(raw)
                extracted = _map_einvoice_claims(parsed_json)
                return QrExtractionResult(
                    found=True,
                    payload_raw=raw,
                    is_jwt=False,
                    qr_signature_status="UNVERIFIED",
                    extracted_fields=extracted,
                    raw_claims=parsed_json
                )
            except Exception:
                pass

        # Plain text QR
        return QrExtractionResult(
            found=True,
            payload_raw=raw,
            is_jwt=False,
            qr_signature_status="NONE",
            extracted_fields={},
            raw_claims={"raw_text": raw}
        )

    return QrExtractionResult(found=False)
