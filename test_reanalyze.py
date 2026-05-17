import os
import json
import requests

from app.inventory_manager_generator import InventoryManagerGenerator

gen = InventoryManagerGenerator()
image_path = "data/uploads/2014_moleca-women-s-polka-dot-bow-flats-size-7-made-in-brazil/IMG_8702.jpg"
if os.path.exists(image_path):
    print("Testing locally...")
    res = gen.generate_options([image_path], strategy="retail")
    print(json.dumps(res, indent=2))
else:
    print("Image not found locally")
