# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Tools:

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Search all listings for articles of clothing that most closely align with your search parameters.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Description of what type of clothing you're looking for
- `size` (str): Size of clothing (S, M, L, etc.)
- `max_price` (float): Maximum price of clothing listing

**What it returns:**
A list of listings that match the description, size, and max_price.

**What happens if it fails or returns nothing:**
Tell the user that there are no matching listings. Try searching something else or adjusting your price range.

---

### Tool 2: suggest_outfit

**What it does:**
Based on the user's wardrobe and a recently searched listing, find a matching listing.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): An item returned by the search_listings function based on the user's input
- `wardrobe` (dict): The user's personal wardrobe which contains items they own

**What it returns:**
The agent should suggest how the user can match the new_item they found with other articles of clothing in their wardrobe

**What happens if it fails or returns nothing:**
If the wardrobe is empty, the agent should tell the user that their wardrobe is empty and suggest some clothes that might be a good match. If no outfit can be suggested, the agent should also try to figure out clothes that can be suggested in order to create an outfit.

---

### Tool 3: create_fit_card

**What it does:**
Returns a piece of text that describes the new item that was suggeseted to the user. It should give a quick little description of the item, the cost, and where it was bought from along with how it ties into the outfit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (dict of dict): A dictionary containing articles of clothing. For example : top: tank top (dict) bottom: jeans (dict)

**What it returns:**
Returns a piece of text that describes the new item that was suggeseted to the user. It should give a quick little description of the item, the cost, and where it was bought from along with how it ties into the outfit. Example: "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories"

**What happens if it fails or returns nothing:**
The agent should return a super generic response that is based on the actual details of the new item. For example: "Hey y'all, I just bought {title} off of {platform} for {price}, check it out on my story!"

---

## Planning Loop:

1. The agent first takes the user's natural language query and uses an LLM strictly formatted to return JSON to extract the core parameters: description, size, and max_price.
2. It passes those parameters into the search_listings tool.
3. The agent checks the results. If the search returns empty, the agent deliberately halts the loop, saves a helpful error message to the session, and exits early to prevent downstream crashes.
4. If results are found, it selects the top match and passes it, along with the user's wardrobe data, into the suggest_outfit tool.
5. It takes the completed outfit text and the original item data, passing both into the create_fit_card tool to generate the final social media caption, completing the session.

## State Management:

When search_listings succeeds, the top dictionary object from the returned list is saved as session["selected_item"].
This exact dictionary object is then passed as the new_item argument into suggest_outfit.
The text returned by the styling tool is saved as session["outfit_suggestion"].
Both session["selected_item"] and session["outfit_suggestion"] are then passed simultaneously into create_fit_card to give the final tool all the context it needs to write the caption.

## Error Handling Strategy:

1. If no items match the query, the tool returns an empty list [] instead of an exception. The agent catches this and returns a polite message asking the user to broaden their search.
2. f the user's wardrobe dictionary is completely empty, the LLM prompt pivots dynamically to suggest pairing the new item with generic, easily accessible basics (for example: white t-shirt or basic jeans).
3. If the outfit string passed into it is empty or entirely whitespace, the tool bypasses the LLM and returns a hardcoded, safe fallback caption utilizing just the item's title, platform, and price.

During deliberate failure testing in the terminal, running search_listings('designer ballgown', size='XXS', max_price=5) successfully and silently returned []

## Spec Reflection:

Spec Helpfulness: Designing the inputs, outputs, and error handling in the planning section not only helped me understand how I wanted the functions to behave but it also helped create documentation for AI to use and actually create those functions. Without the planning phase being so rigorous, we may have had functions implemented in ways that I would not have wanted them to behave.

Implementation diverged: Initially I had planned that when the user didn't have any matching outfits with the item that was picked that the agent would suggest them new items to purchase in order to complete an outfit. I later decided that this would be a very complicated process and as a result, I decided to ditch that idea and instead come up with a much cheaper solution which is suggesting the user to wear generic items such as a white t-shirt or jeans.

## AI Usage:
AI Coding: I used Claude to help me implement functions in tools.py, agent.py, and app.py. I provided detailed context and what exactly I wanted the output to be with the support of my original planning inside of planning.md.

Groq: I integrated Groq's llama-3.3-70b-versatile API directly into the application code to handle dynamic reasoning as well as parameter gathering. It acts as the parser in run_agent, suggests how a user should style their outfit in suggest_outfit, and generates a block of text for the user to post in create_fit_card.