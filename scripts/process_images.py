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
HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "stable-diffusion-v1-5/stable-diffusion-inpainting"
)
GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"
GPT_MODEL = "gpt-4o"

# ─── Environment Variables ────────────────────────────────────────────────────
def load_env() -> dict:
    """Load and validate all required environment variables."""
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

    return {
        "models_token": models_token,
        "hf_token": hf_token,
        "shop_info": shop_info,
    }


# ─── Step 1: Analyze image with GPT-4o via GitHub Models ─────────────────
def analyze_image_with_gpt4o(image_path: Path, shop_info: dict, models_token: str) -> dict:
    """Use GPT-4o (GitHub Models) to find best empty region and suggest shop text.

    Returns dict with keys: x1, y1, x2, y2 (0-1 normalized), and prompt_text.
    """
    log.info("[GPT-4o] Analyzing: %s", image_path.name)

    client = OpenAI(
        base_url=GITHUB_MODELS_BASE_URL,
        api_key=models_token,
    )

    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        buffer = BytesIO()
        img_rgb.save(buffer, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

    shop_name = shop_info.get("shop_name", "Shop")
    phone = shop_info.get("phone", "")
    location = shop_info.get("location", "")
    tagline = shop_info.get("tagline", "")

    system_prompt = "You are an expert in visual design and image composition. Respond ONLY with valid JSON, no markdown fences, no extra text."

    user_prompt = f"""Analyze this image and find the BEST empty/neutral area to place shop branding.
The area should be:
- Relatively empty (sky, wall, floor, background, etc.)
- Large enough for text overlay
- Not covering the main subject of the image

Shop information to display:
- Shop Name: {shop_name}
- Phone: {phone}
- Location: {location}
- Tagline: {tagline}

Respond ONLY in valid JSON:
{{
  "x1": <float 0-1, left edge>,
  "y1": <float 0-1, top edge>,
  "x2": <float 0-1, right edge>,
  "y2": <float 0-1, bottom edge>,
  "prompt_text": "<inpainting prompt, e.g. 'professional shop sign: {shop_name}, {phone}, clean white background, elegant typography'>"
}}

The box must be at least 0.15 wide and 0.10 tall."""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ],
            },
        ],
        max_tokens=512,
        temperature=0.2,
    )

    text = response.choices[0].message.content.strip()
    # Strip potential markdown fences just in case
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    result = json.loads(text)

    # Validate & clamp coordinates
    for key in ("x1", "y1", "x2", "y2"):
        result[key] = max(0.0, min(1.0, float(result[key])))

    # Ensure x2 > x1 and y2 > y1
    if result["x2"] <= result["x1"]:
        result["x2"] = min(1.0, result["x1"] + 0.25)
    if result["y2"] <= result["y1"]:
        result["y2"] = min(1.0, result["y1"] + 0.15)

    log.info(
        "[GPT-4o] Region: x1=%.2f y1=%.2f x2=%.2f y2=%.2f",
        result["x1"], result["y1"], result["x2"], result["y2"],
    )
    log.debug("[GPT-4o] Prompt text: %s", result["prompt_text"])
    return result


# ─── Step 2: Create inpainting mask ──────────────────────────────────────────
def create_mask(image_path: Path, coords: dict) -> Image.Image:
    """Create a white-on-black PIL mask image for the target region."""
    log.info("[Mask] Creating mask for region")

    with Image.open(image_path) as img:
        width, height = img.size

    mask = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(mask)

    x1 = int(coords["x1"] * width)
    y1 = int(coords["y1"] * height)
    x2 = int(coords["x2"] * width)
    y2 = int(coords["y2"] * height)

    draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))
    log.info("[Mask] Pixel region: (%d,%d) -> (%d,%d)", x1, y1, x2, y2)
    return mask


# ─── Step 3: Inpainting via Hugging Face ─────────────────────────────────────
def inpaint_with_huggingface(
    image_path: Path,
    mask: Image.Image,
    prompt_text: str,
    hf_token: str,
) -> Image.Image:
    """Send original image + mask to HF Stable Diffusion Inpainting API."""
    log.info("[HF] Sending inpainting request for: %s", image_path.name)

    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        orig_size = img_rgb.size
        img_buffer = BytesIO()
        img_rgb.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

    mask_buffer = BytesIO()
    mask.save(mask_buffer, format="PNG")
    mask_bytes = mask_buffer.getvalue()

    headers = {"Authorization": f"Bearer {hf_token}"}
    files = {
        "inputs": ("image.png", img_bytes, "image/png"),
        "mask": ("mask.png", mask_bytes, "image/png"),
    }
    data = {"parameters": json.dumps({"prompt": prompt_text, "num_inference_steps": 30})}

    response = requests.post(HF_API_URL, headers=headers, files=files, data=data, timeout=120)

    if response.status_code == 200:
        result_img = Image.open(BytesIO(response.content)).convert("RGB")
        if result_img.size != orig_size:
            result_img = result_img.resize(orig_size, Image.LANCZOS)
        log.info("[HF] Inpainting successful")
        return result_img
    else:
        error_msg = response.text[:500]
        raise RuntimeError(f"HF API error {response.status_code}: {error_msg}")


# ─── Step 4: Save output ─────────────────────────────────────────────────────
def save_output(result_img: Image.Image, original_path: Path) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / original_path.name
    result_img.save(output_path)
    log.info("[Save] Saved to: %s", output_path)
    return output_path


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def process_image(image_path: Path, env: dict) -> bool:
    """Full pipeline for a single image. Returns True on success."""
    try:
        log.info("━━━ Processing: %s ━━━", image_path.name)

        coords = analyze_image_with_gpt4o(
            image_path, env["shop_info"], env["models_token"]
        )
        mask = create_mask(image_path, coords)
        result_img = inpaint_with_huggingface(
            image_path, mask, coords["prompt_text"], env["hf_token"]
        )
        save_output(result_img, image_path)

        log.info("✅ Done: %s", image_path.name)
        return True

    except Exception as e:
        log.error("❌ Failed to process %s: %s", image_path.name, e, exc_info=True)
        return False


def main():
    log.info("🚀 AI Image Processor starting (GPT-4o via GitHub Models)...")

    try:
        env = load_env()
    except (EnvironmentError, ValueError) as e:
        log.error("Environment error: %s", e)
        sys.exit(1)

    log.info("Shop: %s", env["shop_info"].get("shop_name", "Unknown"))

    if not INPUT_DIR.exists():
        log.warning("input/ directory not found. Creating it.")
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = [
        p for p in INPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_FORMATS
    ]

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
