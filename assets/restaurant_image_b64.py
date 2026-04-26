#!/usr/bin/env python3
"""
صورة مطعم الركن الجميل — مُشفّرة بـ Base64
يمكن استخدام هذا الملف مباشرة في facebook_publisher.py
"""

import base64

# صورة المطعم مُشفّرة بـ Base64
# لاستخدامها: from assets.restaurant_image_b64 import get_image_bytes
RESTAURANT_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAABYAAAAMACAIAAAASU1SbAAAAiXpUWHRSYXcgcHJvZmlsZSB0eXBlIGlwdGMAAAiZTYwxDgIxDAT7vOKekDjrtV1T0VHwgbtcIiEhgfh/QaDgmGlWW0w6X66n5fl6jNu9p+ULkapDENgzpj+Kl5aFfa6KnYWgSjZjGOiSYRxTY..."


def get_image_bytes() -> bytes:
    """إرجاع الصورة كـ bytes جاهزة للرفع على فيسبوك"""
    return base64.b64decode(RESTAURANT_IMAGE_B64)
