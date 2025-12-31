import easyocr
import pypdf
import io
from typing import List

# Initialize EasyOCR reader once (it loads the model into memory)
# 'en' for English. Add other languages if needed.
reader = easyocr.Reader(['en'], gpu=True)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file.
    First tries standard text extraction.
    If that yields little text (scanned PDF), falls back to OCR on extracted images.
    """
    text = ""
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        # 1. Try text extraction
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # 2. If text is sparse, try OCR on images within the PDF
        if len(text.strip()) < 50:
            print("PDF text extraction yielded low results. Attempting OCR on embedded images...")
            ocr_text = ""
            for page in pdf_reader.pages:
                for image_file_object in page.images:
                    try:
                        # image_file_object.data contains bytes
                        ocr_result = reader.readtext(image_file_object.data, detail=0)
                        ocr_text += " ".join(ocr_result) + "\n"
                    except Exception as img_err:
                        print(f"Failed to OCR image: {img_err}")
            
            if ocr_text.strip():
                text += "\n" + ocr_text

    except Exception as e:
        print(f"Error reading PDF: {e}")
        # If it fails as a PDF, it might be an image file renamed as PDF? 
        # Unlikely but we can try treating bytes as image directly if pypdf failed completely.
        try:
            print("Attempting to treat file as raw image...")
            result = reader.readtext(file_bytes, detail=0)
            text = " ".join(result)
        except:
            pass
    
    return text

def extract_text_from_images(file_bytes: bytes) -> str:
    """
    Direct OCR on image bytes (jpg/png).
    """
    try:
        result = reader.readtext(file_bytes, detail=0)
        return " ".join(result)
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""
