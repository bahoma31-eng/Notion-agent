#!/usr/bin/env python3
"""AI Image Processor: Analyzes images with GPT-4o via GitHub Models,
then uses Stable Diffusion inpainting to add shop branding."""

import os
import json
import base64
import logging
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw
from openai import OpenAI

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")

# HuggingFace standard model inference endpoint (base64 JSON payload)
HF_MODEL = "runwayml/stable-diffusion-inpainting"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"
GPT_MODEL = "gpt-4o"

# Max dimension for inpainting (SD requires multiples of 8, 512 is optimal)
MAX_INPAINT_SIZE = 512


# ─── Environment Variables ────────────────────────────────────────────────────
def load_env() -> dict:
    models_token = os.environ.get("MODELS_TOKEN", "").strip()
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    shop_info_raw = os.environ.get("SHOP_INFO", "").strip()

    missing = []
    if not models_token:
        missing.append("MODELS_TOKEN")
    if not hf_token:
        missing.append("HF_TOKEN")
    if not shop_info_raw:
        missing.append("SHOP_INFO")
    if missing:
        raise EnvironmentError(f"Missing required secrets: {', '.join(missing)}")

    try:
        shop_info = json.loads(shop_info_raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"SHOP_INFO is not valid JSON: {e}") from e

    return {"models_token": models_token, "hf_token": hf_token, "shop_info": shop_info}


# ─── Step 1: Analyze image with GPT-4o via GitHub Models ─────────────────
def analyze_image_with_gpt4o(image_path: Path, shop_info: dict, models_token: str) -> dict:
    """Use GPT-4o to find best empty region and suggest inpainting prompt."""
    log.info("[GPT-4o] Analyzing: %s", image_path.name)

    client = OpenAI(base_url=GITHUB_MODELS_BASE_URL, api_key=models_token)

    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        buf = BytesIO()
        img_rgb.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode()

    shop_name = shop_info.get("shop_name", "Shop")
    phone = shop_info.get("phone", "")
    location = shop_info.get("location", "")
    tagline = shop_info.get("tagline", "")

    user_prompt = f"""Analyze this image and find the BEST empty/neutral area (sky, wall, floor, background) to place shop branding. The area must NOT cover the main subject.

Shop: {shop_name} | Phone: {phone} | Location: {location} | Tagline: {tagline}

Respond ONLY in valid JSON (no markdown):
{{"x1":<float 0-1>,"y1":<float 0-1>,"x2":<float 0-1>,"y2":<float 0-1>,"prompt_text":"<inpainting prompt describing a professional shop sign with the shop name, phone number, on a clean white background with elegant typography>"}}
Box must be at least 0.15 wide and 0.10 tall."""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "You are a visual design expert. Respond ONLY with valid JSON, no markdown."},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            ]},
        ],
        max_tokens=512,
        temperature=0.2,
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    result = json.loads(text)
    for key in ("x1", "y1", "x2", "y2"):
        result[key] = max(0.0, min(1.0, float(result[key])))
    if result["x2"] <= result["x1"]:
        result["x2"] = min(1.0, result["x1"] + 0.25)
    if result["y2"] <= result["y1"]:
        result["y2"] = min(1.0, result["y1"] + 0.15)

    log.info("[GPT-4o] Region: x1=%.2f y1=%.2f x2=%.2f y2=%.2f",
             result["x1"], result["y1"], result["x2"], result["y2"])
    return result


# ─── Step 2: Create inpainting mask ──────────────────────────────────────────
def create_mask(image_path: Path, coords: dict) -> Image.Image:
    """Create a white-on-black PIL mask for the target region."""
    with Image.open(image_path) as img:
        width, height = img.size

    mask = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(mask)
    x1, y1 = int(coords["x1"] * width), int(coords["y1"] * height)
    x2, y2 = int(coords["x2"] * width), int(coords["y2"] * height)
    draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))
    log.info("[Mask] Pixel region: (%d,%d) -> (%d,%d)", x1, y1, x2, y2)
    return mask


def _pil_to_b64_png(img: Image.Image) -> str:
    """Convert PIL image to base64-encoded PNG string."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _resize_for_inpainting(img: Image.Image) -> Image.Image:
    """Resize to fit within MAX_INPAINT_SIZE, dimensions divisible by 8."""
    w, h = img.size
    if max(w, h) <= MAX_INPAINT_SIZE:
        # Still ensure divisible by 8
        new_w = (w // 8) * 8
        new_h = (h // 8) * 8
        if new_w == w and new_h == h:
            return img
        return img.resize((new_w, new_h), Image.LANCZOS)
    scale = MAX_INPAINT_SIZE / max(w, h)
    new_w = (int(w * scale) // 8) * 8
    new_h = (int(h * scale) // 8) * 8
    return img.resize((new_w, new_h), Image.LANCZOS)


# ─── Step 3: Inpainting via HuggingFace models endpoint (JSON + base64) ────
def inpaint_with_huggingface(
    image_path: Path,
    mask: Image.Image,
    prompt_text: str,
    hf_token: str,
) -> Image.Image:
    """POST to HF standard models endpoint with base64 JSON payload."""
    log.info("[HF] Sending inpainting request to: %s", HF_API_URL)

    with Image.open(image_path) as img:
        orig_size = img.size
        img_resized = _resize_for_inpainting(img.convert("RGB"))

    mask_resized = mask.resize(img_resized.size, Image.NEAREST).convert("L")
    log.info("[HF] Input size: %s -> resized: %s", orig_size, img_resized.size)

    payload = {
        "inputs": prompt_text,
        "parameters": {
            "image": _pil_to_b64_png(img_resized),
            "mask_image": _pil_to_b64_png(mask_resized),
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        },
    }

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }

    response = requests.post(
        HF_API_URL,
        headers=headers,
        json=payload,
        timeout=180,
    )

    log.info("[HF] Response status: %d | Content-Type: %s",
             response.status_code, response.headers.get("Content-Type", "unknown"))

    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        if "image" in content_type:
            # Response is raw image bytes
            result_img = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            # Try JSON with base64
            resp_json = response.json()
            if isinstance(resp_json, list):
                img_data = resp_json[0].get("generated_image") or resp_json[0].get("image")
            else:
                img_data = resp_json.get("generated_image") or resp_json.get("image")
            result_img = Image.open(BytesIO(base64.b64decode(img_data))).convert("RGB")

        if result_img.size != orig_size:
            result_img = result_img.resize(orig_size, Image.LANCZOS)
        log.info("[HF] Inpainting successful")
        return result_img

    elif response.status_code == 503:
        # Model is loading
        try:
            wait = response.json().get("estimated_time", 30)
        except Exception:
            wait = 30
        raise RuntimeError(f"HF model is loading, retry in ~{wait}s (503). Re-run the workflow.")
    else:
        raise RuntimeError(f"HF API error {response.status_code}: {response.text[:600]}")


# ─── Step 4: Save output ─────────────────────────────────────────────────────
def save_output(result_img: Image.Image, original_path: Path) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / original_path.name
    result_img.save(output_path)
    log.info("[Save] Saved to: %s", output_path)
    return output_path


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def process_image(image_path: Path, env: dict) -> bool:
    try:
        log.info("━━━ Processing: %s ━━━", image_path.name)
        coords = analyze_image_with_gpt4o(image_path, env["shop_info"], env["models_token"])
        mask = create_mask(image_path, coords)
        result_img = inpaint_with_huggingface(image_path, mask, coords["prompt_text"], env["hf_token"])
        save_output(result_img, image_path)
        log.info("✅ Done: %s", image_path.name)
        return True
    except Exception as e:
        log.error("❌ Failed to process %s: %s", image_path.name, e, exc_info=True)
        return False


def main():
    log.info("🚀 AI Image Processor starting (GPT-4o + HF Inpainting)...")
    try:
        env = load_env()
    except (EnvironmentError, ValueError) as e:
        log.error("Environment error: %s", e)
        sys.exit(1)

    log.info("Shop: %s", env["shop_info"].get("shop_name", "Unknown"))

    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = [p for p in INPUT_DIR.iterdir()
              if p.is_file() and p.suffix.lower() in SUPPORTED_FORMATS]

    if not images:
        log.info("No images found in input/. Nothing to do.")
        sys.exit(0)

    log.info("Found %d image(s) to process.", len(images))
    results = {img.name: process_image(img, env) for img in sorted(images)}

    successes = sum(results.values())
    failures = len(results) - successes
    log.info("\n📊 Summary: %d succeeded, %d failed", successes, failures)
    if failures > 0:
        log.warning("Failed: %s", ", ".join(n for n, ok in results.items() if not ok))
    if successes == 0 and failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
