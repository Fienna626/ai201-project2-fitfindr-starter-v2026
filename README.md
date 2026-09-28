# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The tools and planning loop are implemented. That last command runs a full
> search, outfit suggestion, and fit-card generation.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a plain-language request for a secondhand clothing item, with
optional size and price limits. It parses the request and searches local
listings, ranking keyword matches while filtering by size and price. If nothing
matches, it explains what the user could change; otherwise, it combines the
selected listing with the user's wardrobe to suggest outfits and write a
shareable fit-card caption. When the wardrobe is empty, it gives general
styling advice instead of assuming the user owns specific pieces.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters listings by the optional inclusive price ceiling and size, then ranks the remaining records by case-insensitive keyword overlap: title matches count 3 points, style-tag matches 2, and description/category/color/brand matches 1; a size matches only when all requested size tokens occur as whole tokens in the listing size.
- **Inputs:** `description` (`str`, required keyword query), `size` (`str | None`, optional), and `max_price` (`float | None`, optional inclusive price ceiling).
- **Returns:** A `list[dict]` of up to `config.SEARCH_RESULT_LIMIT` listing records, highest score first; each record has `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** An empty `list` if the description has no searchable words or no listing passes the filters with at least one keyword match; it never returns `None` for no matches.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two ways to style a selected listing, using named pieces from the wardrobe when available and general advice when it is empty.
- **Inputs:** `new_item` (`dict`, a listing record) and `wardrobe` (`dict`, with an `items` key containing wardrobe-item dictionaries with `name`, `category`, `colors`, `style_tags`, and optional `notes`).
- **Returns:** A non-empty `str` containing outfit advice; if the model returns blank text, a short local styling suggestion is returned instead.
- **When it has nothing:** An empty `wardrobe["items"]` is not an error: the model is asked for general advice without claiming the user owns specific pieces. A model-service failure raises `ModelUnavailable`, which `run_agent` catches and stores in the session's `error` field.

### `create_fit_card`

- **What it does:** Uses the model to write a natural two-to-four sentence social caption about the thrift find and outfit, mentioning the item's title, price, and platform.
- **Inputs:** `outfit` (`str`, the outfit suggestion) and `new_item` (`dict`, a listing record with `title`, `price`, and `platform`).
- **Returns:** A non-empty `str` containing the generated caption; if the model returns blank text, a local caption fallback includes the item title, price, platform, and outfit.
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns a descriptive one-sentence message about the item without calling the model. A model-service failure raises `ModelUnavailable`, which `run_agent` catches and stores in the session's `error` field.

**Spec check:** Could someone implement each tool from this inventory without asking what the inputs, filters, result fields, or empty cases mean? Yes: those behaviors and the exact search ranking weights are specified above.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` with suggestions to change the keywords, size, or price limit and stop before calling either model-backed tool. Otherwise, put the first result in `session["selected_item"]` and pass it with the wardrobe to `suggest_outfit`, then pass its result and the same listing to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex extracts an optional price ceiling (`under`, `below`, `less than`, `up to`, `max`, or `$amount`) and an optional `size`; the remaining text is the description.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → `selected_item` and `wardrobe` → `outfit_suggestion` → `fit_card`; early-stop or model errors are stored in `error`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

Outfit:   Here are two easy, cool ways to style your new vintage graphic tee:

**1. 90s Grunge Streetwear**
*   **Bottoms:** Baggy straight-leg jeans (dark wash) with the brown leather belt
*   **Outerwear:** Vintage black denim jacket (worn over the tee)
*   **Shoes & Bag:** Black combat boots and the black crossbody bag
*   *Why it works:* Playing with textures (faded cotton tee, black denim jacket, and leather boots) gives you that effortless 90s rocker vibe.

**2. Casual High-Low Mix**
*   **Bottoms:** Wide-leg khaki trousers
*   **Layering (Optional):** Tie the oversized grey crewneck sweatshirt loosely around your shoulders if it gets chilly
*   **Shoes:** Chunky white sneakers
*   *Why it works:* Pairing the grungy, boxy graphic tee with clean khaki trousers creates a cool contrast between polished and streetwear.

Fit card: Scored this worn-in Graphic Tee — 2003 Tour Bootleg Style for just $24, and it’s the ultimate lazy-day staple. I love it paired with baggy dark wash denim, or dressed up a bit with wide-leg khakis. Grab it over on my Depop before it's gone!

0 model calls this session, 2 served from cache

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; matches=search_listings('graphic tee', size='M', max_price=30); empty=search_listings('designer ballgown', size='XXS', max_price=5); print('matches:', [(item['id'], item['size'], item['price']) for item in matches], 'empty:', empty)"
matches: [('lst_002', 'S/M', 18.0), ('lst_017', 'S/M', 15.0)] empty: []

```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_empty_wardrobe; item=next(item for item in load_listings() if item['id']=='lst_006'); print(suggest_outfit(item, get_empty_wardrobe()))"
That vintage graphic tee is a fantastic find! Because of its slightly boxy, worn-in fit, here are two easy ways to style it:

**1. The Off-Duty Grunge Look**
Pair the tee with high-waisted baggy denim (think light wash or distressed) and a pair of chunky black sneakers or retro skate shoes. Add a silver chain necklace to lean into the effortless streetwear vibe.

**2. High-Low Contrast**
Tuck the tee loosely into a midi-length satin slip skirt in black, olive, or champagne. Finish the outfit with leather combat boots to balance the edgy graphic with a touch of texture.

```

```
$ python -c "import config; config.CACHE_ENABLED=False; from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[5]; outfit='Pair the tee with baggy denim, a silver chain, and combat boots.'; first=create_fit_card(outfit,item); second=create_fit_card(outfit,item); third=create_fit_card(outfit,item); print('TRY 1:',first); print('TRY 2:',second); print('TRY 3:',third)"
TRY 1: Scored this 2003 Tour Bootleg Style Graphic Tee for just $24 on Depop and honestly, it’s the ultimate find. I styled it with baggy denim, a chunky silver chain, and combat boots for that effortless grunge look.
TRY 2: Found this perfect Graphic Tee — 2003 Tour Bootleg Style for just $24. I styled it with baggy denim, a silver chain, and combat boots for an effortless grunge look. Snagged it on depop and it's already a wardrobe staple.
TRY 3: Nothing beats a perfectly worn-in band tee. I styled this Graphic Tee — 2003 Tour Bootleg Style with baggy denim and combat boots for that ultimate 90s grunge look. Snagged it on depop for just $24.

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Copilot to implement outfit suggestions using the saved wardrobe, including the empty-wardrobe case.
- *What came back:* The first formatter looked for singular `color` and `style` fields, but the wardrobe schema uses `colors` and `style_tags`.
- *What I changed:* I checked `data/wardrobe_schema.json`, corrected the formatter to use the actual fields, and tested the empty-wardrobe path to confirm it returned general styling advice.

**Moment 2**

- *What I asked for:* I asked Copilot to test the impossible-query path using “designer ballgown size XXS under five dollars.”
- *What came back:* Search stopped correctly, but the parser only recognizes numeric price amounts, so the written-out phrase did not become a maximum price.
- *What I changed:* I changed the test query to the documented numeric form, `under $5`, and reran it. The session then showed `max_price: 5.0`, an empty `search_results`, and `fit_card` still set to `None`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
