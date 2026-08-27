"""AI-search matching logic.

This is a deliberately transparent, explainable weighted-scoring function —
not a black-box ML model — so `match_reason` can always point to the exact
criteria that drove a result's score. Swapping this for a real recommender
later only touches this one function; every view/serializer already expects
a `(property, score, reason)` triple back from `score_properties`.
"""

from dataclasses import dataclass

from .models import Property


@dataclass
class ScoredProperty:
    property: Property
    score: int
    reason: str


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def score_properties(queryset, criteria: dict, limit: int) -> list[ScoredProperty]:
    """Score every property in `queryset` against the questionnaire
    `criteria` dict (see AISearchRequestSerializer) and return the top
    `limit`, highest score first.

    Weighting (out of 100): budget fit 35, bedrooms 20, property type 15,
    amenities overlap 15, pet-friendliness 10, transport access 5. A
    property that matches nothing still scores a small base amount so
    results never look artificially harsh.
    """
    min_budget = criteria.get("min_budget")
    max_budget = criteria.get("max_budget")
    bedrooms = criteria.get("bedrooms")
    property_type = criteria.get("property_type")
    wanted_amenities = set(criteria.get("amenities") or [])
    wants_transport = bool(criteria.get("needs_public_transport"))
    wants_pets = bool(criteria.get("pet_friendly"))

    scored: list[ScoredProperty] = []

    for prop in queryset:
        score = 10  # base score
        reasons: list[str] = []

        # --- Budget (35 pts) ---------------------------------------------
        price = float(prop.price)
        if min_budget is not None and max_budget is not None:
            if min_budget <= price <= max_budget:
                score += 35
                reasons.append("within your budget")
            else:
                span = max(max_budget - min_budget, 1)
                distance = min(abs(price - min_budget), abs(price - max_budget))
                score += max(0, 35 - int(35 * distance / span))
        elif max_budget is not None and price <= max_budget:
            score += 35
            reasons.append("within your budget")

        # --- Bedrooms (20 pts) ---------------------------------------------
        if bedrooms and bedrooms not in ("any", ""):
            try:
                wanted_beds = int(str(bedrooms).replace("+", ""))
                if prop.bedrooms == wanted_beds or ("+" in str(bedrooms) and prop.bedrooms >= wanted_beds):
                    score += 20
                    reasons.append(f"{prop.bedrooms}-bedroom match")
            except ValueError:
                pass
        else:
            score += 10

        # --- Property type (15 pts) -----------------------------------------
        if property_type and property_type not in ("any", ""):
            if prop.property_type == property_type:
                score += 15
                reasons.append(f"matches your preferred {prop.get_property_type_display().lower()} type")
        else:
            score += 8

        # --- Amenities overlap (15 pts) --------------------------------------
        if wanted_amenities:
            have = {a.key for a in prop.amenities.all()}
            overlap = wanted_amenities & have
            if overlap:
                score += int(15 * len(overlap) / len(wanted_amenities))
                reasons.append(f"has {len(overlap)}/{len(wanted_amenities)} amenities you asked for")

        # --- Pet friendly (10 pts) -----------------------------------------
        if wants_pets:
            if prop.pet_friendly:
                score += 10
                reasons.append("pet friendly")
        else:
            score += 5

        # --- Transport (5 pts) -----------------------------------------------
        if wants_transport and prop.near_public_transport:
            score += 5
            reasons.append("close to public transport")

        score = _clamp(score)
        reason = "Great match: " + ", ".join(reasons) if reasons else "A solid alternative worth a look"
        scored.append(ScoredProperty(property=prop, score=score, reason=reason))

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:limit]
