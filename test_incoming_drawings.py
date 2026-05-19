import fitz

doc = fitz.open("incoming_b3f8def6.pdf")
page = doc[0]
drawings = page.get_drawings()
print(f"Found {len(drawings)} drawings")
if drawings:
    min_x = min(d['rect'].x0 for d in drawings)
    min_y = min(d['rect'].y0 for d in drawings)
    max_x = max(d['rect'].x1 for d in drawings)
    max_y = max(d['rect'].y1 for d in drawings)
    print(f"Drawing Bounding Box: Rect({min_x}, {min_y}, {max_x}, {max_y})")
