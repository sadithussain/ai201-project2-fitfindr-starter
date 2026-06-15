import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# ── Tool 1: search_listings Tests ──────────────────────────────────────────

def test_search_returns_results():
    """Test the happy path where matches are found."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    """Failure mode: Query matches nothing. Should return empty list, not crash."""
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   

def test_search_price_filter():
    """Ensure the price filter works correctly."""
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item.get("price", 0) <= 10 for item in results)


# ── Tool 2: suggest_outfit Tests ───────────────────────────────────────────

def test_suggest_outfit_normal_wardrobe():
    """Test happy path with a fully populated wardrobe."""
    new_item = {"title": "Vintage Band Tee", "description": "Faded black tee", "style_tags": ["vintage", "grunge"]}
    wardrobe = get_example_wardrobe()
    
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    """Failure mode: The user has an empty wardrobe. Should return generic advice."""
    new_item = {"title": "Vintage Band Tee", "description": "Faded black tee", "style_tags": ["vintage", "grunge"]}
    wardrobe = get_empty_wardrobe()
    
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0


# ── Tool 3: create_fit_card Tests ──────────────────────────────────────────

def test_create_fit_card_normal():
    """Test happy path where a valid outfit string is provided."""
    new_item = {"title": "Chunky Loafers", "price": 40.0, "platform": "Poshmark"}
    outfit = "Pair these with your wide-leg khaki trousers and a white ribbed tank top."
    
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    """Failure mode: Outfit string is empty or whitespace. Should return generic fallback."""
    new_item = {"title": "Chunky Loafers", "price": 40.0, "platform": "Poshmark"}
    
    # Test with a completely empty string
    result_empty = create_fit_card("", new_item)
    assert "Chunky Loafers" in result_empty
    assert "Poshmark" in result_empty
    assert "$40.00" in result_empty
    
    # Test with a whitespace-only string (another common failure state)
    result_whitespace = create_fit_card("   ", new_item)
    assert "Chunky Loafers" in result_whitespace
    assert "Poshmark" in result_whitespace
    assert "$40.00" in result_whitespace