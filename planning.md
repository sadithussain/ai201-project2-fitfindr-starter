# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

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

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
1) The agent will analyze the user's prompt and from it extract a description of the item they're looking for, the size, and a maximum price.
2) Those parameters will be fed into the search_listings tool and the agent will then analyze the reuslt.
2.1) If nothing is returned, the agent will explain to the user that no articles of clothing that match their criteria was found.
3) The agent will use the list of clothings found and call suggest_outfit with the first clothing in the return list.
3.1) If no outfit can be suggested, the agent will say that no outfit can be suggested and then suggest the user on other items to buy to complete the outfit.
4) If an outfit is returned, the agent will describe the outfit, each piece, and what theme / how the outfit will look. The agent will then call create_fit_card with the user's suggested outfit in order to create a piece of text that the user can upload on social media. This should be the last step in the planning loop.

---

## State Management

**How does information from one tool get passed to the next?**
When search_listings returns a list of items, the top item is then saved as the current_item using SessionState.
When suggest_outfit successfully returns an outfit, it can be saved as current_outfit using SessionState.
When create_fit_card successfully returns a fit, it can be saved as current_fit using SessionState.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The agent should halt the loop and apologize to the user and explain that no article of clothing matched the user's description. The agent should suggest the user to increase their budget or broaden their search terms |
| suggest_outfit | Wardrobe is empty | The agent should pivot to suggest generic clothes (for example: white t-shirt, jeans, etc.) to go with the suggested item and explain that an entire outfit was not able to be made with the user's wardrobe. If the user is only missing pants that prevent them from making a complete outfit, fill it in with generic jeans. On the other hand if the user is missing only a shirt, fill it in with a generic white shirt. |
| create_fit_card | Outfit input is missing or incomplete | The agent falls back to generating a generic caption focused only on the newly found item and its price/platform, omitting the rest of the outfit styling |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User query
    │
    ▼
Planning Loop ───────────────────────────────────────────┐
    │                                                    │
    ├─► search_listings(description, size, max_price)    │
    │       │ results=[]                                 │
    │       ├──► [ERROR] "No listings found..." → return │
    │       │                                            │
    │       │ results=[item, ...]                        │
    │       ▼                                            │
    │   Session: selected_item = results[0]              │
    │       │                                            │
    ├─► suggest_outfit(selected_item, wardrobe)          │
    │       │                                            │
    │   Session: outfit_suggestion = "..."               │
    │       │                                            │
    └─► create_fit_card(outfit_suggestion, selected_item)│
            │                                            │
        Session: fit_card = "..."                        │
            │                                            └─ error path returns here
            ▼
        Return session

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
AI Tool: Claude 3.5 Sonnet - High
Input: I will provide Claude with the Tools and Error Handling sections outlined in this document. I will also provide dummy schemas for the data structures so that Claude will know what each data structure has and can use.
Expected Output: Three standalone Python functions (search_listings, suggest_outfit, and create_fit_card). These functions will contain many try/except statements to ensure that proprer error handling protocol is followed.
Verification: We can use simple print statements to check the output of each function given various inputs. We can provide both good and bad inputs to see if correct error handling procedure is followed.

**Milestone 4 — Planning loop and state management:**
AI Tool: Claude 3.5 Sonnet - High
Input: I will provide Claude with the Planning Loop, State Management, and Architecture sections from this document. I will also provide the functions that were created in Milestone 3.
Expected Output: A main script that sequences the tool calls correctly, and handles the logic flow if Tool 1 fails so it doesn't unnecessarily trigger Tool 2 or 3.
Verification: I will run a script with one perfect prompt. I will try asking the agent to find me "Y2K Baby Tee — Butterfly Print" from the listings.json database. The agent should trigger all tools. Then, I will run the script with a bad prompt which should fail on tool 1.

---

## A Complete Interaction (Step by Step)

A user will ask FitFindr what article of clothing they're looking for. The agent will then search listings for the closest matching article of clothing and suggest it as part of the user's outfit. The agent will also return a fit card which is a way for the user to share their outfit on social media.

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent parses the query and calls search_listings(description="vintage graphic tee", max_price=30.0, size="M") (assuming size M default if unknown). The tool queries the mock database and returns a match: {"title": "90s Faded Nirvana Tee", "price": 25.00, "platform": "Depop"}. This is saved to the session state.

**Step 2:**
The agent extracts the user's current context ("baggy jeans and chunky sneakers") to act as the wardrobe. It calls suggest_outfit(new_item={"title": "90s Faded Nirvana Tee"...}, wardrobe={"bottoms": "baggy jeans", "shoes": "chunky sneakers"}). The tool returns a styling suggestion highlighting how the oversized fit of the tee perfectly balances the baggy jeans, creating a cohesive 90s streetwear look.

**Step 3:**
The agent takes the generated outfit and calls create_fit_card(outfit={"top": "90s Faded Nirvana Tee", "bottoms": "baggy jeans", "shoes": "chunky sneakers"}). The tool formulates a social-media-ready caption based on the item details and outfit vibes.

**Final output to user:**
I found a great match for you: a 90s Faded Nirvana Tee for $25.00 on Depop!

How to style it:
Because you already wear baggy jeans and chunky sneakers, this tee is going to fit perfectly into a 90s skater/streetwear aesthetic. Let the shirt hang loose over the jeans, and let the chunky sneakers ground the outfit so you don't look top-heavy.

Your Fit Card for the Gram:
thrifted this faded Nirvana tee off Depop for $25 and honestly it was made for my baggy jeans & chunky kicks 🖤 full look in my stories
