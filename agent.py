"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import config
import trace
from tools import suggest_outfit, create_fit_card
from mcp_client import call_tool
from generate import ModelUnavailable
import re


def _parse_query(query: str) -> dict:
    """Extract a free-text description, optional size, and price ceiling."""
    remaining = query
    max_price = None
    price_pattern = re.compile(
        r"(?:\b(?:under|below|less\s+than|up\s+to|max(?:imum)?(?:\s+price)?)\s*"
        r"\$?\s*(\d+(?:\.\d{1,2})?)|\$\s*(\d+(?:\.\d{1,2})?))",
        re.IGNORECASE,
    )
    price_match = price_pattern.search(remaining)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        remaining = price_pattern.sub(" ", remaining)

    size_pattern = re.compile(
        r"\b(?:in\s+)?size\s*[:=]?\s*([a-z]{1,3}(?:\s*/\s*[a-z]{1,3})?|\d{1,3})\b",
        re.IGNORECASE,
    )
    size_match = size_pattern.search(remaining)
    size = None
    if size_match:
        size = re.sub(r"\s+", "", size_match.group(1)).upper()
        remaining = size_pattern.sub(" ", remaining)

    description = re.sub(r"[^a-zA-Z0-9]+", " ", remaining).strip()
    return {"description": description, "size": size, "max_price": max_price}


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

     The loop is deliberately a small state machine: each tool's result is saved
     to the session before deciding what to do next. An empty search ends the
     run before either model-backed tool is called.
    """
    session = new_session(query, wardrobe)

    stage = "parse"
    iteration = 0
    while stage != "done":
        iteration += 1
        trace.check_iterations(iteration)

        try:
            if stage == "parse":
                session["parsed"] = _parse_query(query)
                trace.step(
                    "parse_query",
                    inputs={"query": query},
                    returned=session["parsed"],
                )
                stage = "search"
            elif stage == "search":
                parsed = session["parsed"]
                search_inputs = {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                }
                session["search_results"] = call_tool("search_listings", search_inputs)
                if not session["search_results"]:
                    trace.step(
                        "search_listings (via MCP)",
                        inputs=search_inputs,
                        returned=session["search_results"],
                        note="empty; stopping before model-backed tools",
                    )
                    description = parsed["description"] or "a clearer item description"
                    session["error"] = (
                        f"No listings matched '{query}'. Try different keywords "
                        f"(for example, {description}) or raise/remove the price "
                        "limit or size filter."
                    )
                    return session
                trace.step(
                    "search_listings (via MCP)",
                    inputs=search_inputs,
                    returned=session["search_results"],
                )
                session["selected_item"] = session["search_results"][0]
                stage = "outfit"
            elif stage == "outfit":
                outfit_inputs = {
                    "new_item": session["selected_item"],
                    "wardrobe": session["wardrobe"],
                }
                try:
                    session["outfit_suggestion"] = suggest_outfit(
                        session["selected_item"], session["wardrobe"]
                    )
                except ModelUnavailable as exc:
                    trace.step(
                        "suggest_outfit",
                        inputs=outfit_inputs,
                        returned=f"ModelUnavailable: {exc}",
                        note="model call failed",
                    )
                    raise
                trace.step(
                    "suggest_outfit",
                    inputs=outfit_inputs,
                    returned=session["outfit_suggestion"],
                )
                stage = "fit_card"
            elif stage == "fit_card":
                fit_card_inputs = {
                    "outfit": session["outfit_suggestion"],
                    "new_item": session["selected_item"],
                }
                try:
                    session["fit_card"] = create_fit_card(
                        session["outfit_suggestion"], session["selected_item"]
                    )
                except ModelUnavailable as exc:
                    trace.step(
                        "create_fit_card",
                        inputs=fit_card_inputs,
                        returned=f"ModelUnavailable: {exc}",
                        note="model call failed",
                    )
                    raise
                trace.step(
                    "create_fit_card",
                    inputs=fit_card_inputs,
                    returned=session["fit_card"],
                )
                stage = "done"
        except ModelUnavailable as exc:
            session["error"] = str(exc)
            return session

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
