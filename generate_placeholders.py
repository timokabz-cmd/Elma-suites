"""
One-time helper: generates placeholder photos so the app has something to
show before you upload real room photos. Not needed once you've added your
own images — you can delete this file any time.

Run with: python generate_placeholders.py
"""
from PIL import Image, ImageDraw
import os

ROOMS = [
    (1, "Standard Single", (91, 130, 175)),
    (2, "Deluxe Double", (175, 122, 91)),
    (3, "Executive Suite", (108, 156, 108)),
    (4, "Family Room", (156, 108, 150)),
]
PHOTOS_PER_ROOM = 5
SIZE = (900, 600)

for room_id, name, color in ROOMS:
    folder = f"images/room_{room_id}"
    os.makedirs(folder, exist_ok=True)
    for i in range(1, PHOTOS_PER_ROOM + 1):
        img = Image.new("RGB", SIZE, color)
        draw = ImageDraw.Draw(img)
        label = f"Room {room_id} - {name}\nPhoto {i}"
        draw.text((40, 40), label, fill=(255, 255, 255))
        img.save(f"{folder}/{i}.jpg", quality=85)

print("Placeholder photos created under images/room_1 ... images/room_4")
