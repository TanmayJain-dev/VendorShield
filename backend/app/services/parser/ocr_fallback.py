import io
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("vendorshield.ocr")

@dataclass
class OCRResult:
    text: str = ""
    engine: str = "none"
    confidence: float = 0.0
    is_scanned: bool = False
    page_count: int = 0
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def is_page_likely_scanned(page, char_threshold: int = 40) -> bool:
    """
    Determines whether a PDF page is a scanned/rasterized image rather than digital vector text.
    If textual characters are fewer than char_threshold but page contains image objects or large drawings.
    """
    try:
        text = page.get_text().strip()
        if len(text) >= char_threshold:
            return False
        
        # Check if page contains embedded images
        image_list = page.get_images(full=True)
        if len(image_list) > 0:
            return True
        
        # Check if page contains vector drawings covering large areas (typical in some scans)
        drawings = page.get_drawings()
        if len(drawings) > 5 and len(text) < char_threshold:
            return True
            
        return len(text) == 0
    except Exception:
        return False


def _try_tesseract(image_bytes: bytes) -> Optional[str]:
    """Attempts OCR via pytesseract if installed and executable configured."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        if text and len(text.strip()) > 0:
            return text.strip()
    except Exception as e:
        logger.debug(f"Pytesseract unavailable or failed: {e}")
    return None


def _try_easyocr(image_bytes: bytes) -> Optional[str]:
    """Attempts OCR via EasyOCR if installed."""
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image_bytes)
        text = " ".join([res[1] for res in results])
        if text and len(text.strip()) > 0:
            return text.strip()
    except Exception as e:
        logger.debug(f"EasyOCR unavailable or failed: {e}")
    return None


def extract_text_from_image(image_bytes: bytes) -> OCRResult:
    """
    Extracts text from a raster image (PNG, JPG, TIFF) via available OCR engines.
    Falls back gracefully if no OCR binaries are installed on the host.
    """
    # 1. Try Tesseract
    tess_text = _try_tesseract(image_bytes)
    if tess_text:
        return OCRResult(
            text=tess_text,
            engine="tesseract",
            confidence=0.88,
            is_scanned=True,
            page_count=1
        )
        
    # 2. Try EasyOCR
    easy_text = _try_easyocr(image_bytes)
    if easy_text:
        return OCRResult(
            text=easy_text,
            engine="easyocr",
            confidence=0.85,
            is_scanned=True,
            page_count=1
        )
        
    return OCRResult(
        text="",
        engine="fallback_null",
        confidence=0.0,
        is_scanned=True,
        page_count=1,
        warnings=["No OCR engine (Tesseract or EasyOCR) is currently installed on host system."]
    )


def process_scanned_pdf(pdf_bytes: bytes) -> OCRResult:
    """
    Processes a PDF detected as scanned or rasterized:
    1. Opens PDF with PyMuPDF
    2. Renders each page to a high-res image (pixmap)
    3. Runs available OCR engine
    4. Aggregates multi-page text
    """
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
            
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return OCRResult(
            text="",
            engine="error",
            confidence=0.0,
            warnings=[f"Failed to open PDF stream for OCR: {str(e)}"]
        )

    all_texts: List[str] = []
    engine_used = "none"
    warnings: List[str] = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        
        # Render page to 300 DPI pixmap for OCR clarity
        zoom = 300 / 72  # 300 DPI scale
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        page_result = extract_text_from_image(img_bytes)
        if page_result.text:
            all_texts.append(f"--- Page {page_idx + 1} ---\n{page_result.text}")
            engine_used = page_result.engine
        if page_result.warnings:
            warnings.extend(page_result.warnings)

    combined_text = "\n\n".join(all_texts)
    confidence = 0.85 if combined_text else 0.0

    return OCRResult(
        text=combined_text,
        engine=engine_used,
        confidence=confidence,
        is_scanned=True,
        page_count=len(doc),
        warnings=list(set(warnings))
    )
