"""
PDF Toolkit - A collection of PDF processing tools

Current tools:
- pdf_to_text: Convert PDF to text using WeChat OCR
- pdf_to_image: Convert PDF to images
- pdf_split_merge: Split, merge and delete PDF pages
- pdf_compress: Compress PDF files
- pdf_to_office: Convert PDF to Word and Excel
- pdf_rotate: Rotate PDF pages
- pdf_watermark: Add a text watermark
- pdf_crypto: Encrypt and decrypt PDF files
"""

from .pdf_to_text import convert_pdf_to_text
from .pdf_to_image import convert_pdf_to_images
from .pdf_split_merge import split_pdf, merge_pdfs, delete_pages
from .pdf_compress import compress_pdf
from .pdf_to_office import convert_pdf_to_word, convert_pdf_to_excel
from .pdf_rotate import rotate_pdf
from .pdf_watermark import add_watermark
from .pdf_crypto import decrypt_pdf, encrypt_pdf

__all__ = [
    "convert_pdf_to_text",
    "convert_pdf_to_images",
    "split_pdf",
    "merge_pdfs",
    "delete_pages",
    "compress_pdf",
    "convert_pdf_to_word",
    "convert_pdf_to_excel",
    "rotate_pdf",
    "add_watermark",
    "encrypt_pdf",
    "decrypt_pdf",
]
__version__ = "0.12.0"