#!/usr/bin/env python3
"""
صورة مطعم الركن الجميل — مُشفّرة بـ Base64
الصورة الأصلية للمطعم مع اسم المطعم مكتوباً عليها
"""
import base64

# استخدام: from assets.restaurant_image_b64 import get_image_bytes
RESTAURANT_IMAGE_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkK"

def get_image_bytes() -> bytes:
    """إرجاع الصورة كـ bytes جاهزة للرفع على فيسبوك"""
    return base64.b64decode(RESTAURANT_IMAGE_B64)
