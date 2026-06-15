"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import os
import json
from groq import Groq

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: Initialize the session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the user's query using Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    system_prompt = (
        "You are an extraction assistant. Extract the clothing description, size, and maximum price "
        "from the user's query. Return a valid JSON object with EXACTLY these three keys: "
        "'description' (string, the core clothing item), "
        "'size' (string, e.g., 'S', 'M', or null if not specified), "
        "'max_price' (float, the price ceiling as a number, or null if not specified)."
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.0 # Keep it deterministic for parsing
        )
        parsed_data = json.loads(response.choices[0].message.content)
    except Exception:
        # Graceful fallback if the LLM parsing fails
        parsed_data = {"description": query, "size": None, "max_price": None}

    session["parsed"] = parsed_data

    # Step 3: Call search_listings with the parsed parameters
    desc = session["parsed"].get("description", query)
    size = session["parsed"].get("size")
    max_price = session["parsed"].get("max_price")

    session["search_results"] = search_listings(description=desc, size=size, max_price=max_price)

    # CRITICAL BRANCH: Check if search returned empty results
    if not session["search_results"]:
        # Set the error and terminate early — do not call the next tools
        session["error"] = (
            "I couldn't find any listings matching your description. "
            "Try broadening your search terms or increasing your budget!"
        )
        return session

    # Step 4: Select the top item
    session["selected_item"] = session["search_results"][0]

    print("\n--- STATE CHECK: SELECTED ITEM ---")
    print(session["selected_item"])

    # Step 5: Call suggest_outfit
    # The selected item state is explicitly passed into the outfit tool
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)

    print("\n--- STATE CHECK: OUTFIT SUGGESTION ---")
    print(session["outfit_suggestion"])

    # Step 6: Call create_fit_card
    # Both the outfit state and item state are passed to the final tool
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])

    # Step 7: Return the completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
