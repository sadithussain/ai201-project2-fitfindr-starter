"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.
    """
    # 1. Load all listings using the provided utility
    all_listings = load_listings()
    
    # Pre-process search query keywords for scoring
    search_keywords = [word.strip(",.?!").lower() for word in description.lower().split() if word.strip(",.?!")]
    if not search_keywords:
        return []

    filtered_listings_with_scores = []

    for item in all_listings:
        # 2. Filter by max_price (inclusive)
        if max_price is not None and item.get("price", 0) > max_price:
            continue
            
        # 2. Filter by size (case-insensitive substring match, e.g., "M" matches "S/M")
        if size is not None:
            item_size = str(item.get("size", "")).lower()
            if size.lower() not in item_size:
                continue

        # 3. Score each remaining listing by keyword overlap with `description`
        score = 0
        
        # Extract text targets from listing fields
        title_text = item.get("title", "").lower()
        desc_text = item.get("description", "").lower()
        style_tags = [tag.lower() for tag in item.get("style_tags", [])]
        
        for keyword in search_keywords:
            # We can award weights based on where the keyword is found
            if keyword in title_text:
                score += 3  # Higher relevance if found in the title
            if keyword in desc_text:
                score += 1  # Standard relevance for body description
            if keyword in style_tags:
                score += 2  # Good relevance for explicit style metadata

        # 4. Drop any listings with a score of 0 (no relevant matches)
        if score > 0:
            filtered_listings_with_scores.append((score, item))

    # 5. Sort by score, highest first, and return only the listing dicts
    filtered_listings_with_scores.sort(key=lambda x: x[0], reverse=True)
    
    return [item for score, item in filtered_listings_with_scores]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    # 1. Initialize the Groq client (requires GROQ_API_KEY in environment)
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Extract details of the new item to feed to the LLM
    item_title = new_item.get("title", "this item")
    item_desc = new_item.get("description", "")
    item_tags = ", ".join(new_item.get("style_tags", []))
    
    item_context = f"Item: {item_title}\nDescription: {item_desc}\nVibe: {item_tags}"

    # 2. Check whether wardrobe['items'] is empty
    wardrobe_items = wardrobe.get("items", [])
    
    if not wardrobe_items:
        # User has an empty wardrobe — pivot to suggesting generic items
        system_prompt = (
            "You are a stylish, straight-talking fashion assistant. "
            "The user is considering buying a new piece of clothing, but their digital wardrobe is currently empty. "
            "Give them a quick, 1-2 paragraph styling suggestion. Since you don't know what they own, "
            "suggest generic, easy-to-find staples (like a plain white t-shirt, classic blue jeans, or standard sneakers) "
            "that would perfectly complete an outfit with this new piece."
        )
        user_prompt = f"Here is the piece I'm thinking about getting:\n{item_context}"
    
    else:
        # 3. User has a wardrobe — format it for the LLM to pull specific combinations
        wardrobe_text = "\n".join([
            f"- {w.get('name')} (Category: {w.get('category')}, Style: {', '.join(w.get('style_tags', []))})"
            for w in wardrobe_items
        ])
        
        system_prompt = (
            "You are a stylish, straight-talking fashion assistant. "
            "The user is considering buying a new piece of clothing and wants to know how to style it using "
            "what they already own in their digital wardrobe. "
            "Suggest 1-2 complete, cohesive outfits combining the new item with pieces specifically named in their wardrobe. "
            "CRITICAL: If their wardrobe is missing an essential category to make a complete outfit (like they have no pants, or no shirts), "
            "fill in the gap by suggesting a generic basic item (e.g., 'a pair of generic straight-leg jeans'). "
            "Keep the response natural, conversational, and under 3 paragraphs."
        )
        user_prompt = (
            f"Here is the piece I'm thinking about getting:\n{item_context}\n\n"
            f"Here is what I currently have in my wardrobe:\n{wardrobe_text}"
        )

    # 4. Call the LLM and return the response
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7, # Give it a little bit of creative freedom for styling
            max_tokens=400
        )
        return chat_completion.choices[0].message.content.strip()
    
    except Exception as e:
        # Ultimate fallback if the API fails or Groq goes down
        return (
            f"I think {item_title} is a great find! I'm having trouble accessing your wardrobe "
            "at the moment, but you can rarely go wrong styling a piece like this with a solid pair "
            "of neutral pants and clean, comfortable shoes."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    # Extract item details safely
    title = new_item.get("title", "this piece")
    price = new_item.get("price", "a steal")
    platform = new_item.get("platform", "the thrift")
    
    # Format the price nicely if it's a number
    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)

    # 1. Guard against an empty or whitespace-only outfit string
    if not outfit or not str(outfit).strip():
        # Fallback to the exact generic response specified in planning.md
        return f"Hey y'all, I just bought {title} off of {platform} for {price_str}, check it out on my story! ✌️"

    # 2. Build the prompt
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are creating a short, shareable outfit caption for Instagram or TikTok. "
        "Write 2-4 sentences that sound casual, authentic, and like a real 'Outfit of the Day' (OOTD) post. "
        "Do NOT sound like a corporate product description. "
        "You MUST naturally mention the item's name, its price, and the platform it was bought on. "
        "Capture the specific vibe of the outfit combination provided by the user. "
        "Include 1-2 relevant emojis, but don't overdo it. Write in lowercase for a more casual aesthetic if it fits the vibe."
    )
    
    user_prompt = (
        f"Item details: Name: {title}, Price: {price_str}, Platform: {platform}\n\n"
        f"Outfit styling vibe: {outfit}\n\n"
        "Write the caption!"
    )

    # 3. Call the LLM and return the response
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.9, # High temperature ensures it sounds different/creative each time
            max_tokens=200
        )
        
        # Strip any accidental quotes the LLM might wrap the caption in
        return chat_completion.choices[0].message.content.strip().strip('"')
        
    except Exception as e:
        # Graceful fallback if the API call fails
        return f"Hey y'all, I just bought {title} off of {platform} for {price_str}, check it out on my story! ✌️"
