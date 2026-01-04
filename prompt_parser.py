import re

def parse_prompt_local(prompt: str):
    """
    Rule-based prompt parser.
    Converts user text into an execution plan.
    """

    prompt_lower = prompt.lower()

    plan = {"actions": []}

    # --- Detect category ---
    category = None
    known_categories = [
        "amazon kindle",
        "amazon fire",
        "amazon echo",
        "christmas products",
        "summer holidays"
    ]

    # for c in known_categories:
    #     if c in prompt_lower:
    #         category = c.title()
    #         break

    category = None
    match = re.search(r"category\s+([a-zA-Z0-9\s]+)", prompt_lower)
    if match:
        category = match.group(1).strip().title()

    # --- Detect months ---
    months = None
    match = re.search(r"next (\d+) months?", prompt_lower)
    if match:
        months = int(match.group(1))

    # --- Detect actions ---
    if "nps" in prompt_lower:
        plan["actions"].append({
            "type": "GET_NPS",
            "category": category,
            "months": None
        })

    if "best" in prompt_lower:
        plan["actions"].append({
            "type": "GET_BEST_PRODUCT",
            "category": category,
            "months": None
        })

    if "worst" in prompt_lower:
        plan["actions"].append({
            "type": "GET_WORST_PRODUCT",
            "category": category,
            "months": None
        })

    if "summary" in prompt_lower or "report" in prompt_lower:
        plan["actions"].append({
            "type": "GET_SUMMARY",
            "category": None,
            "months": None
        })

    if "forecast" in prompt_lower or "future" in prompt_lower or "next" in prompt_lower:
        plan["actions"].append({
            "type": "FORECAST",
            "category": category,
            "months": months if months else 3
        })

    if "graph" in prompt_lower or "plot" in prompt_lower:
        plan["actions"].append({
            "type": "GET_GRAPH",
            "category": category,
            "months": months if months else 3
        })

    if len(plan["actions"]) == 0:
        return None

    return plan
