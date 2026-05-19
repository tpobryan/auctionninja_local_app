import fitz

src_doc = fitz.open("test_label.pdf")
src_page = src_doc[0]

# Fake a crop_rect that is landscape
crop_rect = fitz.Rect(39, 92, 333, 523) # Width 294, Height 431. This is Portrait.

out_doc = fitz.open()
out_page = out_doc.new_page(width=288, height=432)

# If crop_rect is landscape, we rotate by 90
rotation = 90 if crop_rect.width > crop_rect.height else 0

out_page.show_pdf_page(out_page.rect, src_doc, 0, clip=crop_rect, rotate=rotation)

out_doc.save("test_4x6.pdf")
