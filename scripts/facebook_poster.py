#!/usr/bin/env python3
"""
سكريبت النشر التلقائي على فيسبوك — مطعم الركن الجميل
يُولّد منشوراً ترويجياً باستخدام OpenAI API ثم ينشره على صفحة الفيسبوك.
"""

import os
import sys

import openai
import requests


# ───────────────────────────── توليد المنشور ─────────────────────────────

PROMPT = """
أنت مسؤول تسويق لمطعم "الركن الجميل" في حي مارافال وهران الجزائر.
المطعم يقدم: بيتزا، سندويشات، برجر، تاكوس، وأكل سريع خفيف.
اكتب منشوراً ترويجياً جذاباً لصفحة فيسبوك المطعم.
- استخدم مزيجاً من العربية الفصحى والدارجة الوهرانية الجزائرية
- أضف إيموجي مناسبة
- اجعله قصيراً وجذاباً (3-5 أسطر)
- تنوع بين: عروض، تشجيع على الزيارة، وصف الأطباق، أجواء المطعم
- لا تكرر نفس المنشور في كل مرة، كن إبداعياً
""".strip()


def generate_post() -> str:
    """توليد نص المنشور عبر OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("❌ خطأ: OPENAI_API_KEY غير موجود في البيئة.")
        sys.exit(1)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": PROMPT},
            ],
            temperature=0.9,
            max_tokens=300,
        )
        if not response.choices:
            raise ValueError("الرد من OpenAI لم يحتوِ على أي خيارات.")
        message = response.choices[0].message.content
        if not message:
            raise ValueError("الرد من OpenAI كان فارغاً.")
        return message.strip()
    except Exception as exc:
        print(f"❌ فشل توليد المنشور عبر OpenAI: {exc}")
        sys.exit(1)


# ───────────────────────────── النشر على فيسبوك ─────────────────────────────

def post_to_facebook(message: str) -> None:
    """نشر المنشور على صفحة فيسبوك عبر Graph API."""
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()

    if not page_id or not access_token:
        print("❌ خطأ: FB_PAGE_ID أو FB_PAGE_ACCESS_TOKEN غير موجود في البيئة.")
        sys.exit(1)

    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {"message": message, "access_token": access_token}

    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        print(f"✅ تم النشر بنجاح: {response.json()}")
    except requests.exceptions.HTTPError as exc:
        print(f"❌ فشل النشر على فيسبوك (HTTP {exc.response.status_code}): {exc.response.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"❌ فشل النشر على فيسبوك: {exc}")
        sys.exit(1)


# ───────────────────────────── النقطة الرئيسية ─────────────────────────────

def main() -> None:
    print("🚀 بدء سكريبت النشر التلقائي — مطعم الركن الجميل")

    # توليد المنشور
    print("✍️  جارٍ توليد المنشور عبر OpenAI...")
    post_text = generate_post()
    print(f"📝 المنشور المُولَّد:\n{post_text}\n")

    # نشره على فيسبوك
    print("📤 جارٍ النشر على صفحة فيسبوك...")
    post_to_facebook(post_text)


if __name__ == "__main__":
    main()
