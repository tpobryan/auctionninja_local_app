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
        rect = page.rect
        
        # A standard A4 is 595 x 842 points (Portrait)
        # Vinted labels are typically printed sideways on the top half of a portrait A4 sheet.
        if rect.width < rect.height:
            # Portrait A4: Crop the top half
            # This yields a Landscape rectangle (595 x 421)
            crop_rect = fitz.Rect(0, 0, rect.width, rect.height / 2.0)
            page.set_cropbox(crop_rect)
            # Rotate 90 degrees to make it Portrait (421 x 595) for thermal printers
            page.set_rotation(90)
        else:
            # Landscape A4: Crop the left half
            # This yields a Portrait rectangle (421 x 595)
            crop_rect = fitz.Rect(0, 0, rect.width / 2.0, rect.height)
            page.set_cropbox(crop_rect)
            # Already portrait, no rotation needed
        
        # Save the new PDF with just the cropped and rotated page
        out_doc = fitz.open()
        out_doc.insert_pdf(doc, from_page=0, to_page=0)
        
        # Apply crop and rotation again just to be completely safe
        out_doc[0].set_cropbox(crop_rect)
        if rect.width < rect.height:
            out_doc[0].set_rotation(90)
            
        out_doc.save(output_path, garbage=4, deflate=True)
        
        out_doc.close()
        doc.close()
        
        logger.info(f"Successfully processed label: {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to process label {input_path}")
        return False
