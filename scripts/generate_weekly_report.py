#!/usr/bin/env python3
"""
Generate a weekly report on the Iran-America-Israel conflict using GitHub Models (Llama 3.3 70B),
save it to plans/weekly_report.md, and email it to the configured recipient.
"""

import json
import os
import smtplib
import urllib.error
import urllib.request
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ---------------------------------------------------------------------------
# GitHub Models (OpenAI-compatible) helper
# ---------------------------------------------------------------------------

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "meta-llama-3.3-70b-instruct"


def call_model(api_key: str, model: str, prompt: str) -> str:
    base_url = os.getenv("OPENAI_BASE_URL", GITHUB_MODELS_ENDPOINT)
    url = f"{base_url}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت محلل سياسي وعسكري متخصص. مهمتك إعداد تقارير موضوعية "
                    "وشاملة باللغة العربية عن الأحداث الجيوسياسية الإقليمية."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 4096,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub Models API HTTP error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub Models API network error: {exc.reason}") from exc

    return out["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Email helper
# ---------------------------------------------------------------------------

def send_email(smtp_user: str, smtp_password: str, recipient: str,
               subject: str, body_text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())
    except smtplib.SMTPAuthenticationError as exc:
        raise SystemExit(f"SMTP authentication failed: {exc}") from exc
    except smtplib.SMTPException as exc:
        raise SystemExit(f"SMTP error: {exc}") from exc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY secret (should be your GitHub PAT with Models access)")

    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    if not smtp_user or not smtp_password:
        raise SystemExit("Missing SMTP_USER or SMTP_PASSWORD secret")

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    today = date.today().isoformat()

    prompt = f"""
اليوم هو {today}.

أعدّ تقريراً أسبوعياً شاملاً باللغة العربية عن آخر الأحداث العسكرية والسياسية المتعلقة
بالصراع الدائر بين إيران وأمريكا وإسرائيل خلال الأسبوع الماضي.

يجب أن يشمل التقرير الأقسام التالية بالضبط (استخدم عناوين Markdown):

# التقرير الأسبوعي: آخر مستجدات الصراع بين إيران وأمريكا وإسرائيل
## التاريخ: {today}

## 1. ملخص الأحداث الرئيسية
(أبرز ما جرى خلال الأسبوع الأخير)

## 2. المواقف الدبلوماسية
(موقف كل طرف: إيران، أمريكا، إسرائيل)

## 3. العمليات العسكرية
(أي عمليات أو ضربات أو مناورات معلنة)

## 4. آخر المستجدات
(أحدث التطورات حتى تاريخ إعداد التقرير)

## 5. تحليل موجز
(تقييم للوضع الراهن والتوقعات القريبة المدى)

## 6. المصادر المقترحة
(اذكر مصادر إخبارية موثوقة للمتابعة)

اكتب التقرير بأسلوب مهني وموضوعي. لا تُبدِ رأياً شخصياً، بل اعتمد على التحليل الموضوعي.
"""

    print(f"Generating weekly report via GitHub Models ({model}) …")
    report_md = call_model(api_key, model, prompt).strip()

    os.makedirs("plans", exist_ok=True)
    report_path = os.path.join("plans", "weekly_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md + "\n")
    print(f"Report saved to {report_path}")

    greeting = (
        "السلام عليكم ورحمة الله وبركاته،\n\n"
        "نرفق إليكم التقرير الأسبوعي الشامل عن آخر مستجدات الصراع بين إيران وأمريكا "
        "وإسرائيل. يُغطّي التقرير الفترة المنتهية بتاريخ "
        f"{today}، ويتضمن أبرز الأحداث العسكرية والسياسية والمواقف الدبلوماسية "
        "وتحليلاً موجزاً للوضع الراهن.\n\n"
        "نأمل أن يكون التقرير مفيداً ومستوفياً لاحتياجاتكم.\n\n"
        "مع التقدير،\n"
        "نظام التقارير الأسبوعية الآلي (مدعوم بـ Llama 3.3 70B عبر GitHub Models)\n"
        "─────────────────────────────────\n\n"
    )
    email_body = greeting + report_md

    subject = "تقرير أسبوعي: آخر مستجدات الحرب بين إيران وأمريكا وإسرائيل"
    recipient = os.getenv("REPORT_RECIPIENT", "bahoma31@gmail.com")

    print(f"Sending email to {recipient} …")
    send_email(smtp_user, smtp_password, recipient, subject, email_body)
    print("Email sent successfully.")


if __name__ == "__main__":
    main()
