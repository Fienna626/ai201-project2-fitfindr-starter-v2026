# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**

I chose 4 of 5 because plain keyword matching can miss a listing when a query
uses a synonym or different phrasing. If all five test queries are guaranteed
to match the search tool's actual keywords, I would expect 5 of 5.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**

With no matching listings, search gives the agent a clear condition to check:
an empty list. It should take the same branch every time, skip `suggest_outfit`,
and ask the user to change the query.

---

## 3. State preserves the selected listing

In a successful run, the listing ID in `session["selected_item"]` matches the
listing ID received by `suggest_outfit` — 5 of 5 tries.


**Why this target:**

The IDs can be compared exactly on each run. A lower target would allow the
agent to suggest an outfit for a different item.

---

## 4. Fit card has correct item details

The fit card includes the selected listing's title, price, and platform
correctly in at least 4 of 5 tries.


**Why this target:**

I would check those three fields against the selected search result each time.
Exact wording can vary, but those details make the card useful and identify
which item it describes. I chose 4 of 5 because the model may occasionally omit
a field; I would treat that miss as something to improve rather than accept as
normal.


---

## 5. Search respects the price ceiling

Given a query with a stated maximum price, the selected listing's price is at
or below that maximum in 5 of 5 tries.


**Why this target:**

Price is a numeric field in the supplied listings, so every selected item can
be checked directly against the user's limit. Choosing an item above it would
violate the user's stated constraint, so there is no useful reason to allow an
exception.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
