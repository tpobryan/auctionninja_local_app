import fitz
doc = fitz.open("test_label.pdf")
page = doc[0]
images = page.get_images(full=True)
print(f"Found {len(images)} images")
for img in page.get_image_info():
    print("Image Rect:", img['bbox'])
