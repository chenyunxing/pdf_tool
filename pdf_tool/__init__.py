"""
PDF Toolkit - A collection of PDF processing tools

Current tools:
- pdf_to_text: Convert PDF to text using WeChat OCR
- pdf_to_image: Convert PDF to images
- pdf_split_merge: Split, merge and delete PDF pages
- pdf_compress: Compress PDF files
- pdf_to_office: Convert PDF to Word and Excel
"""

from .pdf_to_text import convert_pdf_to_text
from .pdf_to_image import convert_pdf_to_images
from .pdf_split_merge import split_pdf, merge_pdfs, delete_pages
from .pdf_compress import compress_pdf
from .pdf_to_office import convert_pdf_to_word, convert_pdf_to_excel

__all__ = ['convert_pdf_to_text', 'convert_pdf_to_images', 'split_pdf', 'merge_pdfs', 'delete_pages', 'compress_pdf', 'convert_pdf_to_word', 'convert_pdf_to_excel']
__version__ = '0.1.0'