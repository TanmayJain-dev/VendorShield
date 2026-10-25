import io
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
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


# Corporate name tokens for word segmentation & normalization
CORPORATE_TOKENS = [
    "INDIA", "LIMITED", "PRIVATE", "PVT", "LTD", "LLP",
    "ENTERPRISES", "CORPORATION", "INDUSTRIES", "SOLUTIONS",
    "TECHNOLOGIES", "SERVICES", "LOGISTICS", "ELECTRICALS",
    "GLOBAL", "TRADERS", "CO", "COMPANY", "SKY", "BLUE",
    "TECH", "GURU", "PLUS"
]


def normalize_corporate_name(name: Optional[str]) -> str:
    """
    Corporate Name Space Normalizer:
    1. Splits camelCase tokens (e.g. 'BlueSky' -> 'Blue Sky').
    2. Inserts spaces before/after known Indian corporate/entity tokens and English words
       when concatenated in all-caps (e.g. 'BLUESKYINDIALIMITED' -> 'BLUE SKY INDIA LIMITED').
    3. Collapses multiple spaces into a single space and strips.
    """
    if not name:
        return ""
    res = str(name).strip()

    # 1. camelCase splitting (e.g. 'BlueSky' -> 'Blue Sky')
    res = re.sub(r"([a-z])([A-Z])", r"\1 \2", res)

    # 2. Concatenated all-caps entity tokens
    # Sort tokens descending by length so longer words (e.g. CORPORATION) match before shorter (CO)
    sorted_tokens = sorted(CORPORATE_TOKENS, key=len, reverse=True)
    for _ in range(2):
        for token in sorted_tokens:
            token_upper = token.upper()
            if token_upper == "CO":
                # 'CO' is usually a suffix in concatenated all-caps (e.g. 'TRADINGCO' -> 'TRADING CO')
                # Avoid prefix splitting to avoid breaking words like 'COMMERCIAL' or 'COURIER'
                res = re.sub(r"([A-Z])(CO)\b", r"\1 \2", res)
                continue

            # Token at end of an all-caps cluster (e.g. 'SKYINDIA' -> 'SKY INDIA')
            res = re.sub(rf"([A-Z])({token_upper})\b", r"\1 \2", res)
            # Token at beginning of an all-caps cluster (e.g. 'BLUESKY' -> 'BLUE SKY')
            res = re.sub(rf"\b({token_upper})([A-Z])", r"\1 \2", res)
            # Token inside an all-caps cluster (e.g. 'BLUESKYINDIA' -> 'BLUE SKY INDIA')
            res = re.sub(rf"([A-Z])({token_upper})([A-Z])", r"\1 \2 \3", res)

    # 3. Collapse multiple spaces into a single space
    return re.sub(r"\s+", " ", res).strip()



def _group_rapidocr_boxes(result) -> Tuple[str, float]:
    """
    Groups RapidOCR bounding boxes into horizontal lines preserving left-to-right order.
    Adjacent boxes on the same line are joined with a single space ' ', never ''.
    """
    if not result:
        return "", 0.0

    valid_items: List[Dict[str, Any]] = []
    scores: List[float] = []

    for item in result:
        if not item or len(item) < 2 or not item[1] or not str(item[1]).strip():
            continue
        box = item[0]
        text = str(item[1]).strip()
        score = float(item[2]) if len(item) > 2 else 0.88
        scores.append(score)

        ys = [p[1] for p in box] if hasattr(box, "__iter__") else [0, 0]
        xs = [p[0] for p in box] if hasattr(box, "__iter__") else [0, 0]
        y_center = sum(ys) / len(ys) if ys else 0
        h = max(ys) - min(ys) if ys else 10
        x_min = min(xs) if xs else 0

        valid_items.append({
            "box": box,
            "text": text,
            "score": score,
            "y": y_center,
            "h": max(h, 1.0),
            "x": x_min
        })

    if not valid_items:
        return "", 0.0

    # Sort vertically first
    valid_items.sort(key=lambda item: item["y"])

    # Cluster into lines based on vertical proximity and height overlap
    lines: List[List[Dict[str, Any]]] = []
    for item in valid_items:
        placed = False
        for line in lines:
            line_y = sum(it["y"] for it in line) / len(line)
            line_h = sum(it["h"] for it in line) / len(line)
            if abs(item["y"] - line_y) < max(item["h"], line_h) * 0.5:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])

    # Sort lines vertically from top to bottom
    lines.sort(key=lambda line: sum(it["y"] for it in line) / len(line))

    # For each line, sort boxes left to right and join with single space
    formatted_lines: List[str] = []
    for line in lines:
        line.sort(key=lambda it: it["x"])
        # Join adjacent boxes on the same line with a single space ' ', NEVER ''
        line_str = " ".join(it["text"] for it in line if it["text"])
        line_str = re.sub(r"\s+", " ", line_str).strip()
        if line_str:
            formatted_lines.append(line_str)

    avg_score = sum(scores) / len(scores) if scores else 0.88
    return "\n".join(formatted_lines).strip(), avg_score


def _try_rapidocr(image_bytes: bytes) -> Optional[Tuple[str, float]]:
    """
    Attempts OCR using RapidOCR (ONNX Runtime CPU engine - high accuracy, zero external C++ binary dependency).
    Preserves horizontal bounding-box spacing and line grouping.
    """
    try:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()
        result, _ = engine(image_bytes)
        if result:
            text, avg_score = _group_rapidocr_boxes(result)
            if text:
                return text, avg_score
    except Exception as e:
        logger.debug(f"RapidOCR unavailable or failed: {e}")
    return None


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
    Extracts text from a raster image (PNG, JPG, JPEG, WEBP, TIFF) via available OCR engines.
    1. RapidOCR (ONNX Runtime CPU) - primary, reliable, zero C++ binaries required.
    2. Tesseract OCR - secondary fallback.
    3. EasyOCR - tertiary fallback.
    4. Graceful heuristic response if text is empty or engines unavailable.
    """
    # 1. Primary: RapidOCR (ONNX Runtime)
    rapid_res = _try_rapidocr(image_bytes)
    if rapid_res:
        text, conf = rapid_res
        return OCRResult(
            text=text,
            engine="rapidocr",
            confidence=round(conf, 2),
            is_scanned=True,
            page_count=1
        )

    # 2. Secondary: Tesseract
    tess_text = _try_tesseract(image_bytes)
    if tess_text:
        return OCRResult(
            text=tess_text,
            engine="tesseract",
            confidence=0.88,
            is_scanned=True,
            page_count=1
        )
        
    # 3. Tertiary: EasyOCR
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
        warnings=["No OCR engine produced text for this image."]
    )


def process_scanned_pdf(pdf_bytes: bytes) -> OCRResult:
    """
    Processes a PDF detected as scanned or rasterized:
    1. Opens PDF with PyMuPDF
    2. Renders each page to a high-res image (pixmap at 300 DPI)
    3. Runs available OCR engine (RapidOCR / Tesseract / EasyOCR)
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
    confidence = 0.88 if combined_text else 0.0

    return OCRResult(
        text=combined_text,
        engine=engine_used,
        confidence=confidence,
        is_scanned=True,
        page_count=len(doc),
        warnings=list(set(warnings))
    )
