"""
Rule-based transaction categorization engine.

Assigns a category string to a transaction based on keyword matching
against its description.  All rules are deterministic and reproducible:
the same description will always produce the same category.

IMPORTANT LIMITATION
--------------------
Keyword matching is *not* semantic understanding.  Two legitimate
transactions with identical descriptions are indistinguishable by these
rules.  Categories should be treated as helpful hints, not authoritative
labels.

Adding or modifying rules
--------------------------
Edit the ``CATEGORY_RULES`` list below.  Each entry is a tuple of
``(category_name, [list_of_keywords])``.  Rules are evaluated in order;
the first matching rule wins.  Keywords are matched case-insensitively
anywhere in the description.  To avoid false positives, prefer specific
multi-word phrases over single common words.

Example::

    ("salary", ["monthly salary", "payroll", "wages"]),

If no rule matches, ``"uncategorized"`` is returned.
"""

import re
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Rule table  —  (category, [keywords ...])
# Rules are tested in the order they appear; first match wins.
# Keywords are matched case-insensitively as whole-word or substring matches.
# ---------------------------------------------------------------------------

CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    # Income categories
    ("salary", ["monthly salary", "payroll", "wages", "salary credit", "salary"]),
    ("investment", ["dividend", "stock sale", "mutual fund", "sip return", "investment return"]),
    # Housing
    ("rent", ["rent payment", "house rent", "landlord", "rental"]),
    # Food & groceries
    ("groceries", ["grocery", "groceries", "supermarket", "vegetables", "fruits", "kirana", "big bazaar", "reliance fresh", "dmart"]),
    # Utilities
    ("utilities", ["electricity bill", "water bill", "internet bill", "broadband", "gas bill", "mobile recharge", "phone bill", "utility"]),
    # Transport
    ("transport", ["petrol", "diesel", "fuel", "uber", "ola", "taxi", "auto rickshaw", "metro", "bus ticket", "train ticket", "flight ticket", "toll"]),
    # Healthcare
    ("healthcare", ["hospital", "clinic", "pharmacy", "medicine", "doctor", "medical", "health insurance", "lab test", "diagnostic"]),
    # Education
    ("education", ["tuition", "school fee", "college fee", "course fee", "books", "stationery", "online course", "exam fee"]),
    # Entertainment
    ("entertainment", ["netflix", "amazon prime", "hotstar", "movie", "cinema", "concert", "streaming", "gaming", "spotify"]),
    # Shopping
    ("shopping", ["amazon", "flipkart", "myntra", "shopping", "online purchase", "clothing", "shoes", "electronics"]),
    # Dining
    ("dining", ["restaurant", "swiggy", "zomato", "food delivery", "cafe", "coffee", "lunch", "dinner", "breakfast"]),
    # Insurance
    ("insurance", ["insurance premium", "life insurance", "car insurance", "health insurance premium", "lic"]),
]

# Compiled patterns for performance: (category, [compiled_regex, ...])
_COMPILED_RULES: List[Tuple[str, List[re.Pattern]]] = [
    (
        category,
        [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords],
    )
    for category, keywords in CATEGORY_RULES
]


def categorize(description: str, supplied_category: Optional[str] = None) -> str:
    """Return the appropriate category for a transaction.

    If ``supplied_category`` is a non-empty string other than
    ``"uncategorized"``, it is returned unchanged — user-supplied categories
    are always preserved.

    Otherwise the description is matched against ``CATEGORY_RULES`` in
    order.  The first matching rule's category is returned.  If no rule
    matches, ``"uncategorized"`` is returned.

    Args:
        description: The transaction description text.
        supplied_category: The category already provided by the user or CSV
            file, if any.  Pass ``None`` or ``"uncategorized"`` to trigger
            auto-categorization.

    Returns:
        A lower-case category string.

    Example::

        categorize("Monthly salary credit")          # -> "salary"
        categorize("Swiggy order #12345")            # -> "dining"
        categorize("Random payment")                 # -> "uncategorized"
        categorize("Random payment", "custom")       # -> "custom"
    """
    # Preserve any explicitly-supplied non-default category.
    if supplied_category and supplied_category.strip().lower() not in ("", "uncategorized"):
        return supplied_category.strip().lower()

    for category, patterns in _COMPILED_RULES:
        for pattern in patterns:
            if pattern.search(description):
                return category

    return "uncategorized"
