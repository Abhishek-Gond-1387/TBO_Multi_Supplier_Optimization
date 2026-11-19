"""AI-Powered Natural Language Travel Assistant & Personalization Engine for TBO Discovery.

Understands free-text natural language travel prompts, extracts structured parameters
(party size, duration, budget, transit, stay, activities), evaluates budget feasibility,
recommends suitable enclaves when generic vibes are described, and generates customized
trip architectures with transparent rationales.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# Number word mapping for party size and duration extraction
WORD_NUMBERS: Dict[str, int] = {
    "one": 1, "solo": 1, "single": 1, "alone": 1, "myself": 1,
    "two": 2, "couple": 2, "pair": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12, "dozen": 12,
    "fifteen": 15,
    "twenty": 20
}

# Known destination clusters for vibe-based recommendation
VIBE_DESTINATIONS: Dict[str, List[Dict[str, str]]] = {
    "mountain": [
        {"name": "Manali, Himachal Pradesh", "reason": "Surrounded by pine forests, Beas River, and high alpine trails ideal for trekking."},
        {"name": "Munnar, Kerala", "reason": "Emerald tea terraces, mist-shrouded hills, and peaceful climate in the Western Ghats."},
        {"name": "Dharamshala & McLeodGanj", "reason": "Tibetan culture, cedar forests, and scenic Triund trek for friends and nature lovers."},
        {"name": "Kasol & Parvati Valley", "reason": "Tranquil riverside villages and accessible day hikes."}
    ],
    "beach": [
        {"name": "Goa (South Sands & Heritage)", "reason": "Pristine secluded beaches in Palolem and Agonda away from commercial crowds."},
        {"name": "Gokarna, Karnataka", "reason": "Serene cliffside beaches (Om Beach, Half Moon) with relaxed bohemian atmosphere."},
        {"name": "Havelock Island, Andamans", "reason": "Crystal white sands, turquoise waters, and scuba diving at Radhanagar Beach."}
    ],
    "heritage": [
        {"name": "Jaipur, Rajasthan", "reason": "UNESCO World Heritage Amber Fort, pink sandstone palaces, and vibrant royal bazaars."},
        {"name": "Udaipur, Rajasthan", "reason": "Historic marble lake palaces and tranquil sunset boat cruises."},
        {"name": "Varanasi, Uttar Pradesh", "reason": "Centuries-old stone ghats, sunrise boat journeys, and spiritual evening aartis."}
    ],
    "wildlife": [
        {"name": "Ranthambore National Park", "reason": "Royal Bengal tiger safaris with ancient 10th-century fort ruins."},
        {"name": "Jim Corbett National Park", "reason": "Dense sal forests, riverine belts, and rich elephant and tiger habitats."},
        {"name": "Kaziranga National Park", "reason": "UNESCO biodiversity reserve home to the world's largest population of one-horned rhinos."}
    ],
    "spiritual": [
        {"name": "Rishikesh & Haridwar", "reason": "Sacred Ganges riverfront, yoga ashrams, and Himalayan foothills."},
        {"name": "Varanasi, Uttar Pradesh", "reason": "Sacred Kashi Vishwanath corridor and ancient river ghats."},
        {"name": "Amritsar, Punjab", "reason": "Golden Temple serenity, communal langar kitchen, and rich heritage."}
    ]
}


def extract_party_size(text: str) -> Dict[str, Any]:
    """Extracts adults, children, infants, party label, and required rooms."""
    lowered = text.casefold()

    adults = 2
    children = 0
    infants = 0
    party_label = "2 Travelers"

    # 1. Solo detection
    if re.search(r"\b(solo|alone|myself|single traveler|1 adult)\b", lowered):
        adults = 1
        party_label = "Solo Traveler"
    # 2. Couple detection
    elif re.search(r"\b(couple|husband and wife|honeymoon|partner|two of us|2 adults)\b", lowered):
        adults = 2
        party_label = "Couple (2 Adults)"
    # 3. Family detection
    elif "family" in lowered:
        fam_match = re.search(r"(\d+)\s*(?:people|members|adults)?\s*family", lowered) or re.search(r"family of (\d+|[a-z]+)", lowered)
        if fam_match:
            raw = fam_match.group(1)
            count = WORD_NUMBERS.get(raw, int(raw) if raw.isdigit() else 4)
            adults = max(2, count - 1)
            children = max(0, count - adults)
            party_label = f"Family of {count}"
        else:
            adults = 2
            children = 2
            party_label = "Family (2 Adults, 2 Kids)"
    # 4. Friends or group detection: e.g. "for four friends", "group of 12", "12 friends", "4 pax"
    else:
        group_match = (
            re.search(r"(\d+|[a-z]+)\s*(?:friends|buddies|colleagues|people|travellers|travelers|members|pax|guys)\b", lowered)
            or re.search(r"group of\s*(\d+|[a-z]+)", lowered)
        )
        if group_match:
            raw = group_match.group(1)
            count = WORD_NUMBERS.get(raw, int(raw) if raw.isdigit() else 2)
            adults = count
            party_label = f"Group of {count} Friends"

    # Explicit child/infant mentions
    child_match = re.search(r"(\d+|[a-z]+)\s*(?:child|children|kids)", lowered)
    if child_match:
        raw_c = child_match.group(1)
        children = WORD_NUMBERS.get(raw_c, int(raw_c) if raw_c.isdigit() else 0)

    infant_match = re.search(r"(\d+|[a-z]+)\s*(?:infant|infants|babies|baby)", lowered)
    if infant_match:
        raw_i = infant_match.group(1)
        infants = WORD_NUMBERS.get(raw_i, int(raw_i) if raw_i.isdigit() else 0)

    total_travelers = adults + children + infants
    if total_travelers == 0:
        total_travelers = 2
        adults = 2

    # Room calculation: standard rule is max 2 adults per room, extra bed for 3rd
    rooms_needed = max(1, (adults + 1) // 2)

    # Vehicle sizing recommendation based on party size
    if total_travelers <= 3:
        vehicle_rec = "Executive Sedan (Dzire / Etios / Camry)"
        transport_capacity_note = "Comfortably accommodates up to 3 passengers with 2 large luggage bags."
    elif total_travelers <= 6:
        vehicle_rec = "Premium SUV (Toyota Innova Crysta)"
        transport_capacity_note = "Spacious 6-seater captain seat arrangement with ample boot space."
    elif total_travelers <= 12:
        vehicle_rec = "Luxury Tempo Traveller (12-Seater Executive Coach)"
        transport_capacity_note = "Dedicated group travel van with push-back seats, separate luggage bay, and AC."
    elif total_travelers <= 20:
        vehicle_rec = "Luxury Mini-Coach (18-20 Seater)"
        transport_capacity_note = "Mid-size luxury coach suitable for large groups with tour manager seating."
    else:
        vehicle_rec = "40-Seater Volvo Luxury Multi-Axle Coach"
        transport_capacity_note = "Full-size commercial coach requiring institutional group coordination."

    return {
        "total_travelers": total_travelers,
        "adults": adults,
        "children": children,
        "infants": infants,
        "rooms_needed": rooms_needed,
        "party_label": party_label,
        "recommended_vehicle": vehicle_rec,
        "capacity_note": transport_capacity_note
    }


def extract_duration(text: str) -> Dict[str, Any]:
    """Extracts duration in days and nights with pacing analysis."""
    lowered = text.casefold()

    days = 5  # default
    # Match patterns like: "4 days", "for three days", "2-day trip", "a week", "15 days", "weekend"
    day_match = (
        re.search(r"(\d+|[a-z]+)\s*[- ]*(?:day|days)\b", lowered)
        or re.search(r"for\s*(\d+|[a-z]+)\s*days?", lowered)
    )
    if day_match:
        raw = day_match.group(1)
        days = WORD_NUMBERS.get(raw, int(raw) if raw.isdigit() else 5)
    elif "weekend" in lowered:
        days = 2 if "long" not in lowered else 3
    elif "week" in lowered:
        days = 7
    elif "month" in lowered:
        days = 30

    days = max(1, min(days, 60))
    nights = max(0, days - 1)

    if days <= 2:
        pacing = "FAST_PACED"
        style_desc = "Focused weekend escape highlighting top 2-3 landmarks without transit fatigue."
    elif days <= 5:
        pacing = "BALANCED"
        style_desc = "Curated discovery with balanced sightseeing, cultural heritage, and relaxed evenings."
    elif days <= 9:
        pacing = "COMPREHENSIVE"
        style_desc = "Regional circuit journey allowing deep cultural exploration and scenic day trips."
    else:
        pacing = "EXTENDED_PANORAMA"
        style_desc = "Grand immersion journey with dedicated leisure rest days and multi-city circuits."

    return {
        "days": days,
        "nights": nights,
        "pacing": pacing,
        "style_desc": style_desc
    }


def extract_budget(text: str, total_travelers: int, days: int) -> Dict[str, Any]:
    """Extracts budget amount, currency, per-person calculations, and feasibility."""
    lowered = text.casefold()

    currency = "INR"
    if "usd" in lowered or "$" in lowered or "dollar" in lowered:
        currency = "USD"
    elif "eur" in lowered or "€" in lowered or "euro" in lowered:
        currency = "EUR"
    elif "gbp" in lowered or "£" in lowered or "pound" in lowered:
        currency = "GBP"
    elif "aed" in lowered or "dirham" in lowered:
        currency = "AED"

    is_per_person = bool(re.search(r"\b(per person|each|per head|a piece)\b", lowered))

    # Look for monetary amounts: ₹15,000, 15000, 15k, 8,000, 3000
    amount = 0.0
    k_match = re.search(r"(?:₹|\$|€|£|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\b", lowered)
    if k_match:
        amount = float(k_match.group(1)) * 1000
    else:
        num_match = re.search(r"(?:budget(?: of)?|under|up to|max(?:imum)?|total(?: of)?|₹|\$|€|£|rs\.?|inr)\s*(?:of\s*)?([0-9,]+)", lowered)
        if num_match:
            amount = float(num_match.group(1).replace(",", ""))

    # If user specifies per person, calculate total
    if is_per_person and amount > 0:
        total_budget = amount * total_travelers
        per_person = amount
    elif amount > 0:
        total_budget = amount
        per_person = amount / max(1, total_travelers)
    else:
        # Realistic default calibrated baseline: ₹6,000/person for 5 days
        per_person = 6500.0 * (days / 5.0)
        total_budget = per_person * total_travelers

    daily_per_person = per_person / max(1, days)

    # Feasibility evaluation
    # Realistic minimum bare minimum per day in India (hostel/homestay + train + basic food): ₹750/person/day
    min_viable_per_day = 850.0
    min_viable_total = min_viable_per_day * days * total_travelers

    if currency == "INR" and total_budget < (min_viable_total * 0.75):
        feasibility_status = "INSUFFICIENT"
        feasibility_alert = (
            f"Budget Notice: Total budget of ₹{int(total_budget):,} equates to ₹{int(daily_per_person):,}/day per person. "
            f"Realistic minimum in this sector (sleeper rail + homestays) is approximately ₹{int(min_viable_total):,}. "
            f"We recommend opting for overnight trains to save hotel nights, community homestays, and self-guided cultural trails."
        )
        recommended_action = "APPLY_BUDGET_SAVING_RECOMMENDATIONS"
    elif currency == "INR" and total_budget < min_viable_total:
        feasibility_status = "BUDGET_TIGHT"
        feasibility_alert = (
            f"Budget Alert: Budget is tight (approx. ₹{int(daily_per_person):,}/day/person). "
            f"We have optimized your plan using Express Trains and boutique homestays with complimentary breakfast."
        )
        recommended_action = "OPTIMIZE_VALUE"
    else:
        feasibility_status = "FEASIBLE"
        feasibility_alert = "Budget is realistic and well-calibrated for quality accommodations and verified experiences."
        recommended_action = "PROCEED_CURATED"

    return {
        "total_budget": round(total_budget),
        "per_person_budget": round(per_person),
        "daily_per_person": round(daily_per_person),
        "currency": currency,
        "is_per_person_input": is_per_person,
        "feasibility_status": feasibility_status,
        "feasibility_alert": feasibility_alert,
        "recommended_action": recommended_action,
        "minimum_viable_total": round(min_viable_total)
    }


def extract_preferences(text: str) -> Dict[str, Any]:
    """Extracts preferred transportation, accommodation, and curated activities."""
    lowered = text.casefold()

    # Transport extraction
    transport = "Optimal Multi-Modal (Train / Flight)"
    if re.search(r"\b(train|railway|rail|vande bharat|tejas)\b", lowered):
        transport = "Train (Indian Railways Express)"
    elif re.search(r"\b(flight|fly|air|airplane)\b", lowered):
        transport = "Commercial Flight"
    elif re.search(r"\b(bus|coach|volvo)\b", lowered):
        transport = "AC Deluxe Bus / Volvo"
    elif re.search(r"\b(self[- ]?drive|rental car|rent a car)\b", lowered):
        transport = "Self-Drive Rental SUV"
    elif re.search(r"\b(chauffeur|cab|taxi|private car|innova)\b", lowered):
        transport = "Private Chauffeur (Innova Crysta)"
    elif re.search(r"\b(bike|motorcycle|bullet|riding)\b", lowered):
        transport = "Motorcycle Expedition"

    # Accommodation extraction
    accommodation = "Curated Boutique Hotel / Heritage Stay"
    if re.search(r"\b(hostel|backpack|dorm)\b", lowered):
        accommodation = "Curated Social Hostel"
    elif re.search(r"\b(homestay|guest house|guesthouse|cottage|village)\b", lowered):
        accommodation = "Authentic Local Homestay"
    elif re.search(r"\b(resort|villa)\b", lowered):
        accommodation = "Luxury Nature Resort & Spa"
    elif re.search(r"\b(camp|camping|glamping|tent)\b", lowered):
        accommodation = "Wilderness Glamping & Camp"
    elif re.search(r"\b(palace|fort|5[- ]?star|five star|luxury|presidential)\b", lowered):
        accommodation = "5-Star Grand Heritage Palace"

    # Activities extraction
    activities = []
    if re.search(r"\b(trek|trekking|hike|hiking)\b", lowered):
        activities.append("Mountain Trekking & Alpine Trails")
    if re.search(r"\b(photo|photography|views|scenic|instagram)\b", lowered):
        activities.append("Landscape Photography & Panoramic Viewpoints")
    if re.search(r"\b(adventure|rafting|paragliding|skiing|safari)\b", lowered):
        activities.append("High Adrenaline Adventure Sports")
    if re.search(r"\b(food|cuisine|culinary|eating|street food|tasting)\b", lowered):
        activities.append("Regional Food Walks & Gastronomy Trails")
    if re.search(r"\b(temple|spiritual|sacred|ghat|meditation|yoga)\b", lowered):
        activities.append("Spiritual Corridors & Sanctuary Visits")
    if re.search(r"\b(history|heritage|monument|fort|palace|museum)\b", lowered):
        activities.append("Architectural Heritage & Historic Palaces")
    if re.search(r"\b(beach|sea|coast|watersports|snorkeling|scuba)\b", lowered):
        activities.append("Coastal Walks & Water Expeditions")
    if re.search(r"\b(peaceful|peace|quiet|relax|relaxing|serene|tranquil)\b", lowered):
        activities.append("Tranquil Nature Retreats & Leisure")

    if not activities:
        activities = ["Cultural Discovery", "Scenic Viewpoints", "Local Gastronomy"]

    return {
        "transportation": transport,
        "accommodation": accommodation,
        "activities": activities
    }


def extract_destination(text: str) -> Tuple[Optional[str], Optional[List[Dict[str, str]]]]:
    """
    Extracts an explicit destination from the text, or identifies a vibe
    and returns recommended destinations with clear rationales.
    """
    lowered = text.casefold()

    # Common explicit destinations
    known = [
        "manali", "jaipur", "srinagar", "goa", "munnar", "varanasi", "leh", "ladakh",
        "udaipur", "delhi", "new delhi", "mumbai", "agra", "rishikesh", "darjeeling",
        "dharamshala", "kasol", "amritsar", "jodhpur", "jaisalmer", "ooty", "shimla",
        "hampi", "mysore", "alleppey", "kochi", "andaman", "havelock", "dubai", "abu dhabi"
    ]

    for dest in known:
        if re.search(rf"\b{re.escape(dest)}\b", lowered):
            return dest.title(), None

    # If no explicit destination, detect vibe
    if re.search(r"\b(mountain|mountains|hills|hill station|snow|valley|highland)\b", lowered):
        return "Manali, Himachal Pradesh", VIBE_DESTINATIONS["mountain"]
    if re.search(r"\b(beach|sea|coast|ocean|island|sand)\b", lowered):
        return "Goa, India", VIBE_DESTINATIONS["beach"]
    if re.search(r"\b(heritage|royal|palace|fort|history|rajasthan)\b", lowered):
        return "Jaipur, Rajasthan", VIBE_DESTINATIONS["heritage"]
    if re.search(r"\b(tiger|wildlife|jungle|national park|safari)\b", lowered):
        return "Ranthambore, Rajasthan", VIBE_DESTINATIONS["wildlife"]
    if re.search(r"\b(spiritual|sacred|peace|ashram|yoga|ganga|ghat)\b", lowered):
        return "Rishikesh, Uttarakhand", VIBE_DESTINATIONS["spiritual"]

    # Fallback default
    return "Jaipur, Rajasthan", None


def parse_natural_language_journey_request(prompt: str) -> Dict[str, Any]:
    """
    Complete end-to-end NLP parser:
    Transforms an unstructured user description into verified, structured travel requirements.
    """
    text = prompt.strip()
    party_info = extract_party_size(text)
    duration_info = extract_duration(text)
    dest, suggestions = extract_destination(text)
    budget_info = extract_budget(text, party_info["total_travelers"], duration_info["days"])
    pref_info = extract_preferences(text)

    # Build personalized rationale explanation
    rationale = (
        f"Customized for a {party_info['party_label'].lower()} for a {duration_info['days']}-day journey to {dest}. "
        f"We allocated {party_info['rooms_needed']} rooms and paired {pref_info['transportation']} with {pref_info['accommodation']}. "
        f"Key highlights include {', '.join(pref_info['activities'][:2])}, maintaining an investment of "
        f"{budget_info['currency']} {budget_info['total_budget']:,} ({budget_info['feasibility_status']})."
    )

    return {
        "status": "SUCCESS",
        "raw_prompt": text,
        "destination": dest,
        "destination_suggestions": suggestions,
        "party": party_info,
        "duration": duration_info,
        "budget": budget_info,
        "preferences": pref_info,
        "personalized_rationale": rationale
    }
