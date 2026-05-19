import fitz

doc = fitz.open("processed_label.pdf")
page = doc[0]
rect = page.rect
print("Crop Rect:", rect)
print("Rotation:", page.rotation)

images = page.get_image_info()
print(f"Found {len(images)} images")
for img in images:
    print("Image Rect:", img['bbox'])
    
words = page.get_text("words")
print(f"Found {len(words)} words")
