import fitz

doc = fitz.open("test_label.pdf")
page = doc[0]
rect = page.rect

images = page.get_image_info()
crop_rect = None

if images:
    largest_img = max(images, key=lambda i: (i['bbox'][2] - i['bbox'][0]) * (i['bbox'][3] - i['bbox'][1]))
    area = (largest_img['bbox'][2] - largest_img['bbox'][0]) * (largest_img['bbox'][3] - largest_img['bbox'][1])
    if area > 10000:
        crop_rect = fitz.Rect(largest_img['bbox'])
        crop_rect = crop_rect + (-10, -10, 10, 10)
        crop_rect.intersect(rect)

if not crop_rect:
    crop_rect = fitz.Rect(0, 0, rect.width, rect.height / 2.0)

print("Crop Rect:", crop_rect)
print("Crop Width/Height:", crop_rect.width, crop_rect.height)

page.set_cropbox(crop_rect)

if crop_rect.width > crop_rect.height:
    print("Rotating 90 degrees")
    page.set_rotation(90)
else:
    print("No rotation needed")
    page.set_rotation(0)

doc.save("output_test.pdf", garbage=4, deflate=True)
