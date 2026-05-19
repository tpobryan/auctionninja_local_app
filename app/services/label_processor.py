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
        
        # Strategy: Find the largest image in the PDF (which is almost always the shipping label itself)
        # and crop exactly to its bounding box, adding a small margin.
        images = page.get_image_info()
        crop_rect = None
        
        if images:
            # Find the largest image by area
            largest_img = max(images, key=lambda i: (i['bbox'][2] - i['bbox'][0]) * (i['bbox'][3] - i['bbox'][1]))
            area = (largest_img['bbox'][2] - largest_img['bbox'][0]) * (largest_img['bbox'][3] - largest_img['bbox'][1])
            
            # If the image is reasonably large (e.g., > 10000 sq points), it's the label
            if area > 10000:
                crop_rect = fitz.Rect(largest_img['bbox'])
                # Add a 10-point safe margin around the label
                crop_rect = crop_rect + (-10, -10, 10, 10)
                # Ensure we don't expand outside the physical page
                crop_rect.intersect(rect)
                
        # Fallback if no large images are found: Crop the top half or top-left
        if not crop_rect:
            if rect.width < rect.height:
                crop_rect = fitz.Rect(0, 0, rect.width, rect.height / 2.0)
            else:
                crop_rect = fitz.Rect(0, 0, rect.width / 2.0, rect.height)
                
        # Create a STRICT 4x6 output document (288 x 432 points)
        # This prevents iOS AirPrint from defaulting to "Envelope" due to weird custom crop dimensions
        out_doc = fitz.open()
        out_page = out_doc.new_page(width=288, height=432)
        
        # Thermal printers expect a Portrait label (Width < Height).
        # If the cropped label is Landscape (Width > Height), rotate it 90 degrees.
        rotation = 90 if crop_rect.width > crop_rect.height else 0
        
        # Paint the cropped section of the original PDF onto our perfectly sized 4x6 page
        out_page.show_pdf_page(out_page.rect, doc, 0, clip=crop_rect, rotate=rotation)
            
        out_doc.save(output_path, garbage=4, deflate=True)
        
        out_doc.close()
        doc.close()
        
        logger.info(f"Successfully processed label: {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to process label {input_path}")
        return False
