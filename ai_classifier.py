"""
Uses Claude (Anthropic API) to read a saved post's caption/note and
suggest the best category from our fixed list.
"""

import os
import json
import anthropic
from models import CATEGORIES

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def classify_caption(caption: str) -> str:
    """
    Sends the caption to Claude and returns one category from CATEGORIES.
    Falls back to "Other" if the caption is empty or the API call fails.
    """
    if not caption or not caption.strip():
        return "Other"

    category_list = ", ".join(CATEGORIES)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify this social media post caption into exactly one of these "
                        f"categories: {category_list}.\n\n"
                        f"Caption: \"{caption}\"\n\n"
                        f"Respond with ONLY the category name, nothing else."
                    ),
                }
            ],
        )
        result = response.content[0].text.strip()

        # Make sure Claude's answer matches one of our known categories exactly
        for cat in CATEGORIES:
            if cat.lower() == result.lower():
                return cat

        return "Other"

    except Exception as e:
        print(f"AI classification failed: {e}")
        return "Other"
