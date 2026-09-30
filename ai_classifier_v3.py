"""
Uses a real (headless) browser via Playwright to render the post page,
so we can grab its actual thumbnail image even though Instagram/Facebook
serve a JS-only shell to plain HTTP requests. The image is then sent to
Claude's vision model for classification - no caption required.
"""

import os
import re
import base64
import requests
import anthropic
from models import CATEGORIES
from playwright.sync_api import sync_playwright

_api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"[DEBUG] API key loaded from environment: {bool(_api_key)}  (length: {len(_api_key) if _api_key else 0})")

client = anthropic.Anthropic(api_key=_api_key)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch_thumbnail(post_url: str):
    """
    Renders the post page with a real headless browser and extracts its
    og:image (preview thumbnail). Returns (image_bytes, mime_type) or
    (None, None) if it can't be found.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(post_url, timeout=20000, wait_until="domcontentloaded")
            # Reels keep streaming video/network activity forever, so we
            # can't wait for "networkidle" - instead just give the page a
            # couple seconds to finish injecting its meta tags.
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()

        print(f"[DEBUG] Rendered page length: {len(html)} chars")
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not match:
            print("[DEBUG] No og:image tag found even after rendering.")
            return None, None

        image_url = match.group(1).replace("&amp;", "&")
        print(f"[DEBUG] Found thumbnail URL: {image_url[:80]}...")

        img_resp = requests.get(image_url, headers=HEADERS, timeout=8)
        img_resp.raise_for_status()

        mime_type = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
        print(f"[DEBUG] Thumbnail downloaded: {len(img_resp.content)} bytes, type {mime_type}")
        return img_resp.content, mime_type

    except Exception as e:
        print(f"[DEBUG] Playwright thumbnail fetch failed: {e}")
        return None, None


def classify_post(post_url: str, caption: str = "") -> str:
    """
    Classifies a saved post primarily by looking at its actual thumbnail
    image, using caption text (if any) as extra context. Always returns
    one of the values in CATEGORIES.
    """
    category_list = ", ".join(CATEGORIES)
    print(f"[DEBUG] classify_post called. URL: {post_url}  Caption: '{caption}'")

    image_bytes, mime_type = fetch_thumbnail(post_url)
    print(f"[DEBUG] Image found: {bool(image_bytes)}")

    content_blocks = []

    if image_bytes:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        content_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": b64_image,
            },
        })

    prompt_text = (
        f"Look at the image above (a thumbnail from a social media post/reel) "
        f"and classify what it actually shows into exactly one of these "
        f"categories: {category_list}.\n\n"
    )
    if caption and caption.strip():
        prompt_text += f'The post\'s caption is: "{caption.strip()}"\n\n'
    prompt_text += (
        "Base your answer mainly on what you SEE in the image, using the "
        "caption only as extra context. Respond with ONLY the category name, "
        "nothing else."
    )
    content_blocks.append({"type": "text", "text": prompt_text})

    # Nothing to work with at all
    if not image_bytes and not (caption and caption.strip()):
        print("[DEBUG] No image and no caption - defaulting to Other.")
        return "Other"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[{"role": "user", "content": content_blocks}],
        )
        result = response.content[0].text.strip()
        print(f"[DEBUG] Claude's raw answer: '{result}'")

        for cat in CATEGORIES:
            if cat.lower() == result.lower():
                return cat

        print(f"[DEBUG] '{result}' did not match any known category, defaulting to Other.")
        return "Other"

    except Exception as e:
        print(f"[DEBUG] AI classification failed with exception: {e}")
        return "Other"
