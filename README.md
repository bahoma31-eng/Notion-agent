# 🖼️ AI Image Processor

Automatic shop branding overlay on product images using **Google Gemini** for smart region detection and **Stable Diffusion Inpainting** for seamless blending.

## ✨ How It Works

1. **Drop images** into the `input/` folder and push to GitHub
2. **Gemini Flash** analyzes each image to find the best empty area for branding
3. **A mask** is generated over that region using Pillow
4. **Stable Diffusion Inpainting** fills the masked area with professional shop branding
5. **Results** are saved to `output/` and committed automatically

## 🚀 Quick Start

### 1. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value | Source |
|---|---|---|
| `GEMINI_API_KEY` | Your Gemini API key | [aistudio.google.com](https://aistudio.google.com) — Free |
| `HF_TOKEN` | Your Hugging Face token | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — Free |
| `SHOP_INFO` | JSON with your shop details | See format below |

### 2. Configure SHOP_INFO

Paste this as the value of the `SHOP_INFO` secret (edit with your info):

```json
{
  "shop_name": "متجر النجوم",
  "phone": "+213 555 123 456",
  "location": "وهران، الجزائر",
  "tagline": "جودة لا تضاهى"
}
```

### 3. Add Images & Push

```bash
# Copy your images to input/
cp my-product-photo.jpg input/

# Commit and push — workflow starts automatically!
git add input/
git commit -m "Add product images for processing"
git push
```

### 4. Collect Results

After the workflow completes (~2-5 min per image), find your branded images in `output/`.

## 📁 Project Structure

```
.
├── .github/workflows/
│   └── image-processor.yml   # GitHub Actions workflow
├── scripts/
│   └── process_images.py     # Main processing script
├── input/                    # Drop your images here
│   └── .gitkeep
├── output/                   # Processed images appear here
│   └── .gitkeep
├── requirements.txt
├── .env.example              # Template for local development
└── README.md
```

## 🔧 Manual Trigger

You can also trigger the workflow manually:
1. Go to **Actions** tab
2. Select **🖼️ AI Image Processor**
3. Click **Run workflow**
4. Optionally enable debug logging

## 🖥️ Local Development

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Create .env file from template
cp .env.example .env
# Edit .env with your actual secrets

# 3. Load env and run
export $(cat .env | xargs)
python scripts/process_images.py
```

## ⚙️ Supported Image Formats

`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| Workflow not triggering | Ensure images are inside `input/` folder |
| `GEMINI_API_KEY` error | Verify secret name matches exactly |
| HF model loading slowly | First run may take 2-3 min for model warm-up |
| Image looks unchanged | Check workflow logs — Gemini region coordinates |
| JSON parse error | Validate `SHOP_INFO` at [jsonlint.com](https://jsonlint.com) |

## 📝 Notes

- Each image is processed **independently** — one failure won't stop others
- The workflow uses `[skip ci]` in the commit message to avoid infinite loops
- Images are committed back to the repo automatically after processing
- Gemini API is free up to 15 RPM on the free tier
- Hugging Face Inference API is free for open models (rate limits apply)
