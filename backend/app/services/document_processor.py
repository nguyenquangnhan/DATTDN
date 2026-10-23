"""NotebookLM Backend - Document Processing Service

Handles extraction of text from PDFs, images (PaddleOCR / Gemini Vision), and URLs.
Also handles text chunking for embedding.
"""

import asyncio
import logging
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz  # PyMuPDF
import httpx
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-load PaddleOCR to avoid slow startup
_ocr_instance = None


def _get_ocr():
    """Lazy-load optimized PaddleOCR instance using lightweight mobile models."""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR

        # Dynamically determine mobile recognition model based on language settings
        det_model = "PP-OCRv4_mobile_det"
        if settings.PADDLE_OCR_LANG == "ch":
            rec_model = "PP-OCRv4_mobile_rec"
        elif settings.PADDLE_OCR_LANG == "en":
            rec_model = "en_PP-OCRv4_mobile_rec"
        else:
            rec_model = "latin_PP-OCRv5_mobile_rec"

        _ocr_instance = PaddleOCR(
            text_detection_model_name=det_model,
            text_recognition_model_name=rec_model,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang=settings.PADDLE_OCR_LANG,
            device="gpu" if settings.PADDLE_USE_GPU else "cpu",
            enable_mkldnn=False, # Disabled to avoid PIR engine errors on Windows CPU
        )
    return _ocr_instance

# ── Helper for parallel PaddleOCR (ProcessPoolExecutor) ──────────────────────


def _ocr_single_page(image_path: str) -> str:
    """OCR a single image page. Designed for ProcessPoolExecutor.

    Each worker process loads its own PaddleOCR instance.
    """
    # Restrict PaddlePaddle to exactly 1 thread per process to prevent thread thrashing
    import os
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"

    ocr = _get_ocr()
    result = ocr.predict(
        image_path,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False
    )

    extracted_lines = []
    if result and isinstance(result, list) and len(result) > 0:
        pred = result[0]
        if isinstance(pred, dict) and "rec_texts" in pred:
            texts = pred["rec_texts"]
            scores = pred.get("rec_scores", [])
            for text, score in zip(texts, scores):
                if score > 0.5:
                    extracted_lines.append(text)
        elif isinstance(pred, list):
            for line in pred:
                if line and len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    if confidence > 0.5:
                        extracted_lines.append(text)

    return "\n".join(extracted_lines)


# ── PDF Processing ────────────────────────────────────────────────────────────


def extract_text_from_pdf(file_path: str) -> dict:
    """Extract text from a PDF file using PyMuPDF.

    Returns:
        dict with keys: text, page_count, metadata
    """
    logger.info(f"Processing PDF: {file_path}")
    doc = fitz.open(file_path)
    page_count = len(doc)
    pages_text = []

    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text.strip())

    full_text = "\n\n".join(pages_text)
    ocr_processed = False

    # Check if text is empty or very short on average (indicating a scanned PDF)
    if not full_text.strip() or len(full_text.strip()) < 10 * page_count:
        logger.info(f"PDF {file_path} has low selectable text density ({len(full_text.strip())} chars for {page_count} pages). Falling back to PaddleOCR.")
        ocr_pages_text = []
        import tempfile
        import os

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                for page_num in range(page_count):
                    page = doc[page_num]
                    # Render page as image (75 DPI is optimal for fast CPU-based OCR processing)
                    pix = page.get_pixmap(dpi=75)
                    temp_img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                    pix.save(temp_img_path)

                    # Extract text using our PaddleOCR helper
                    ocr_res = extract_text_from_image(temp_img_path)
                    page_text = ocr_res.get("text", "")
                    ocr_pages_text.append(page_text)

            ocr_full_text = "\n\n".join(ocr_pages_text)
            if ocr_full_text.strip():
                full_text = ocr_full_text
                ocr_processed = True
                logger.info("Successfully extracted text from scanned PDF using PaddleOCR fallback.")
        except Exception as ocr_err:
            logger.error(f"Failed to run PaddleOCR fallback on PDF: {ocr_err}")

    doc.close()

    return {
        "text": full_text,
        "page_count": page_count,
        "metadata": {
            "source_type": "pdf",
            "file_path": file_path,
            "ocr_processed": ocr_processed,
        },
    }


# ── Image Processing (PaddleOCR) ─────────────────────────────────────────────


def extract_text_from_image(file_path: str) -> dict:
    """Extract text from an image using optimized PaddleOCR pipeline.

    Returns:
        dict with keys: text, metadata
    """
    logger.info(f"Processing image with optimized local PaddleOCR: {file_path}")
    ocr = _get_ocr()

    result = ocr.predict(
        file_path,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False
    )

    extracted_lines = []
    if result and isinstance(result, list) and len(result) > 0:
        pred = result[0]
        # In PaddleOCR 2.8+, predict returns a dictionary with 'rec_texts' and 'rec_scores'
        if isinstance(pred, dict) and "rec_texts" in pred:
            texts = pred["rec_texts"]
            scores = pred.get("rec_scores", [])
            for text, score in zip(texts, scores):
                if score > 0.5:
                    extracted_lines.append(text)
        # Fallback to the old list-of-tuples format in case it behaves differently in some contexts
        elif isinstance(pred, list):
            for line in pred:
                if line and len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    if confidence > 0.5:
                        extracted_lines.append(text)

    full_text = "\n".join(extracted_lines)
    return {
        "text": full_text,
        "page_count": 1,
        "metadata": {
            "source_type": "image",
            "file_path": file_path,
            "ocr_lines": len(extracted_lines),
            "ocr_method": "paddleocr_optimized",
        },
    }


# ── Gemini Vision OCR (Async + Concurrent) ───────────────────────────────────

# Lazy-load Gemini client
_gemini_client = None


def _get_gemini_client():
    """Lazy-load the Google GenAI client."""
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


async def _ocr_page_with_gemini(image_path: str) -> str:
    """Use Gemini Vision API to extract text from a single image."""
    client = _get_gemini_client()
    img = Image.open(image_path)

    response = await client.aio.models.generate_content(
        model=settings.CHAT_MODEL,
        contents=[
            img,
            "Extract all text from this image exactly as written. "
            "Return only the raw text content, preserving the original layout. "
            "Do not add any commentary, explanation, or formatting markers.",
        ],
    )

    return response.text.strip() if response.text else ""


async def extract_text_from_pdf_async(file_path: str) -> dict:
    """Optimized async PDF text extraction using local parallel PaddleOCR.

    Pipeline:
    1. Try selectable text first (instant)
    2. For scanned PDFs: Render pages at 75 DPI (low resolution for fast CPU processing)
    3. Run optimized local PaddleOCR in parallel across CPU cores using ProcessPoolExecutor.
    """
    logger.info(f"Processing PDF (async): {file_path}")
    doc = fitz.open(file_path)
    page_count = len(doc)

    # Step 1: Try selectable text
    pages_text = []
    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text.strip())

    full_text = "\n\n".join(pages_text)

    if full_text.strip() and len(full_text.strip()) >= 10 * page_count:
        doc.close()
        return {
            "text": full_text,
            "page_count": page_count,
            "metadata": {"source_type": "pdf", "file_path": file_path, "ocr_processed": False},
        }

    # Step 2: Scanned PDF - convert all pages to images (at 75 DPI for speed)
    logger.info(
        f"PDF {file_path} has low text density ({len(full_text.strip())} chars for {page_count} pages). "
        "Running local parallel PaddleOCR..."
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = []
        for page_num in range(page_count):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=75) # 75 DPI is optimal for fast CPU-based OCR
            img_path = os.path.join(temp_dir, f"page_{page_num}.png")
            pix.save(img_path)
            image_paths.append(img_path)
        doc.close()

        # Step 3: Run PaddleOCR in parallel with ProcessPoolExecutor
        cpu_count = os.cpu_count() or 4
        # Cap at 3 workers to keep execution on fast Performance cores and avoid E-core bottlenecks
        max_workers = min(cpu_count, page_count, 3)
        logger.info(f"Running parallel PaddleOCR OCR with {max_workers} worker processes...")

        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                loop.run_in_executor(executor, _ocr_single_page, img_path)
                for img_path in image_paths
            ]
            ocr_pages_text = await asyncio.gather(*futures)

        paddle_text = "\n\n".join(ocr_pages_text)
        logger.info(f"Finished parallel local OCR: {len(paddle_text)} characters extracted.")
        return {
            "text": paddle_text,
            "page_count": page_count,
            "metadata": {
                "source_type": "pdf",
                "file_path": file_path,
                "ocr_processed": True,
                "ocr_method": "paddleocr_parallel_optimized",
            },
        }


async def extract_text_from_image_async(file_path: str) -> dict:
    """Extract text from a single image using local optimized PaddleOCR."""
    return extract_text_from_image(file_path)


# ── URL Processing ───────────────────────────────────────────────────────────


async def extract_text_from_url(url: str) -> dict:
    """Extract text content from a URL using httpx + BeautifulSoup.

    Returns:
        dict with keys: text, metadata
    """
    logger.info(f"Processing URL: {url}")

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unwanted elements
    for element in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()

    # Get page title
    title = soup.title.string if soup.title else url

    # Extract main content
    # Try to find main content area first
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(role="main")
        or soup.find("div", class_="content")
        or soup.body
    )

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    clean_text = "\n".join(lines)

    return {
        "text": clean_text,
        "page_count": None,
        "metadata": {
            "source_type": "url",
            "url": url,
            "title": title,
        },
    }


# ── Text Chunking ────────────────────────────────────────────────────────────


def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
    """Split text into chunks using LangChain RecursiveCharacterTextSplitter.

    Args:
        text: The text to split
        chunk_size: Size of each chunk (default from settings)
        chunk_overlap: Overlap between chunks (default from settings)

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks
