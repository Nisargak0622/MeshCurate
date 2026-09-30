"""
Uses Claude (Anthropic API, vision-capable) to look at the actual photo/video
thumbnail of a saved post and classify it - not just the caption text.

How it works:
1. Fetch the post's public page HTML and pull out its og:image (thumbnail).
2. Download that thumbnail image.
3. Send the image (and caption, if any) to Claude and ask it to classify
   what it actually SEES into one of our fixed categories.
4. If no thumbnail can be found (private post, blocked, etc.), fall back
   to classifying from the caption text alone, or "Other" if nothing
   at all is available.
"""

import os
import re
import base64
import requests
import anthropic
from models import CATEGORIES

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch_thumbnail(post_url: str):
    """
    Downloads the post's public page and extracts its og:image (preview
    thumbnail). Returns (image_bytes, mime_type) or (None, None) if it
    can't be found.
    """
    try:
        page = requests.get(post_url, headers=HEADERS, timeout=8)
        print(f"[DEBUG] Page fetch status: {page.status_code}, length: {len(page.text)} chars")

        match = re.search(r'<meta property="og:image" content="([^"]+)"', page.text)
        if not match:
            print("[DEBUG] No og:image tag found on the page (likely blocked/login wall).")
            return None, None

        image_url = match.group(1).replace("&amp;", "&")
        print(f"[DEBUG] Found thumbnail URL: {image_url[:80]}...")

        img_resp = requests.get(image_url, headers=HEADERS, timeout=8)
        img_resp.raise_for_status()

        mime_type = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
        print(f"[DEBUG] Thumbnail downloaded: {len(img_resp.content)} bytes, type {mime_type}")
        return img_resp.content, mime_type

    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Thumbnail fetch failed: {e}")
        return None, None


def classify_post(post_url: str, caption: str = "") -> str:
    """
    Classifies a saved post by looking at its actual thumbnail image
    (preferred) plus any caption text provided. Always returns one of
    the values in CATEGORIES.
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

    # If we have neither an image nor a caption, there's nothing to classify
    if not image_bytes and not (caption and caption.strip()):
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
