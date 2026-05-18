import fitz
doc = fitz.open("test_label.pdf")
page = doc[0]
rect = page.rect
print("Original Rect:", rect)
print("Rotation:", page.rotation)

words = page.get_text("words")
if words:
    min_x = min(w[0] for w in words)
    min_y = min(w[1] for w in words)
    max_x = max(w[2] for w in words)
    max_y = max(w[3] for w in words)
    print(f"Content Bounding Box: ({min_x}, {min_y}, {max_x}, {max_y})")
else:
    print("No text words found.")
