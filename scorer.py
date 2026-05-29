"""
Signal scoring module - separates scoring logic from collection
"""


HIGH_INTENT_KEYWORDS = {
    "website hacked": 30,
    "email hacked": 30,
    "business email compromised": 35,
    "website down": 25,
    "wordpress hacked": 35,
    "domain expired": 40,
    "dns issue": 30,
    "mx records": 35,
    "ransomware": 50,
    "server outage": 25,
    "microsoft 365 down": 25,
    "email not working": 20,
    "ddos attack": 45,
    "data breach": 50,
    "ssl certificate": 25,
    "apache down": 20,
    "nginx down": 20,
}

BUSINESS_HINTS = [
    "restaurant", "company", "business", "owner", "shop", "store",
    "agency", "clinic", "dentist", "law firm", "startup", "local business",
    "small business", "hotel", "bank", "office",
]

US_HINTS = [
    "texas", "florida", "california", "new york", "usa", "u.s.",
    "american", "county", "city", "united states",
]


def calculate_score(title: str, summary: str = None, link: str = None) -> tuple:
    """
    Calculate priority score for a signal based on keywords and context.
    
    Args:
        title: Article title
        summary: Article summary/description
        link: Source URL
    
    Returns:
        (score, matched_keywords)
    """
    score = 0
    matched = []
    
    text = f"{title} {summary or ''} {link or ''}".lower()
    
    # High intent keyword scoring
    for keyword, points in HIGH_INTENT_KEYWORDS.items():
        if keyword in text:
            score += points
            matched.append(keyword)
    
    # Business relevance boost
    for hint in BUSINESS_HINTS:
        if hint in text:
            score += 15
            break  # Only count once
    
    # US geo boost
    for hint in US_HINTS:
        if hint in text:
            score += 10
            break  # Only count once
    
    # Urgency boost
    if "urgent" in text or "asap" in text or "critical" in text:
        score += 25
    
    return score, matched


def should_collect(score: int, threshold: int = 40) -> bool:
    """Check if signal meets collection threshold"""
    return score >= threshold
