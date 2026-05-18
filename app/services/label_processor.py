import fitz  # PyMuPDF
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def process_vinted_label(input_path: str | Path, output_path: str | Path) -> bool:
    """
    Processes a Vinted A4 shipping label PDF.
    Crops the top-left portion (the actual label) and saves it as a 4x6 ready PDF.
    """
    try:
        input_path = str(input_path)
        output_path = str(output_path)
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False

        # Open the PDF
        doc = fitz.open(input_path)
        if len(doc) == 0:
            logger.error("The provided PDF has no pages.")
            return False

        # Get the first page
        page = doc[0]
        
        # A standard A4 is 595 x 842 points.
        # A standard 4x6 label is 288 x 432 points.
        # Usually Vinted labels are positioned in the top left or top center.
        # We will crop a rectangle that safely encompasses a standard shipping label in the top left.
        # X0, Y0, X1, Y1. We'll use 400 x 600 points (about 5.5 x 8.3 inches) to be safe and ensure the barcode isn't cut off.
        # The Rollo printer driver will scale this down to 4x6.
        # For a more exact 4x6 aspect ratio: 400 x 600 is exactly 4:6.
        
        crop_rect = fitz.Rect(0, 0, 400, 600)
        
        # Ensure we don't crop larger than the page itself
        page_rect = page.rect
        crop_rect.intersect(page_rect)
        
        # Set the new cropbox
        page.set_cropbox(crop_rect)
        
        # Save the new PDF with just the cropped page
        # We create a new document to ensure only the single cropped page is saved
        out_doc = fitz.open()
        out_doc.insert_pdf(doc, from_page=0, to_page=0)
        
        # Apply the cropbox again in the new doc just in case
        out_doc[0].set_cropbox(crop_rect)
        
        out_doc.save(output_path, garbage=4, deflate=True)
        
        out_doc.close()
        doc.close()
        
        logger.info(f"Successfully processed label: {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to process label {input_path}")
        return False
