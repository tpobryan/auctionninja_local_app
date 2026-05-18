import fitz
doc = fitz.open()
page = doc.new_page(width=595, height=842)
print("Rotation:", page.rotation)
try:
    page.set_rotation(90)
    print("New Rotation:", page.rotation)
except Exception as e:
    print("Error:", repr(e))
