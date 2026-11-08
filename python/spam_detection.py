import re

# Explainable screening: multiple independent signals reduce false positives.
SCAM_PATTERNS = [
    (r'\b(?:guaranteed|guarantee)\s+(?:daily\s+)?(?:profit|income|returns?|earnings?)\b|\b(?:daily|profit|income)\s+(?:profit|income\s+)?guaranteed\b', 'Guaranteed profit or income claim'),
    (r'\bearn\s+(?:\$|₹|rs\.?\s*)?\d[\d,]*(?:\s*(?:daily|per\s+day|a\s+day|weekly|per\s+week))?', 'Unrealistic earnings claim'),
    (r'(?:\$|₹|\brs\.?\s*)\s?\d[\d,]*.*\b(?:one day|daily|working from home|work from home|crypto)\b', 'Money-making claim tied to a high-risk context'),
    (r'(?:\b(?:get featured|feature me|promote my page)\b.{0,60}@\w+|@\w+.{0,60}\b(?:get featured|feature me|promote my page)\b)', 'Engagement promotion using a tagged account'),
    (r'\bfollow\s+@\w+.{0,80}\buse\s+code\b', 'Follow-and-discount engagement bait'),
    (r'\b(?:you have won|you won|winner selected|claim your|free\s+(?:iphone|phone|gift|prize|money))\b', 'Prize or giveaway bait'),
    (r'\bclick\s+(?:the\s+)?(?:link|here|below)\b', 'Urgent click-through language'),
    (r'\b(?:dm|message|contact)\s+me\s+(?:now\s+)?to\s+(?:earn|win|recover|claim|get)\b', 'Direct-message solicitation'),
    (r'\b(?:recover|unlock|verify)\s+your\s+(?:hacked|blocked|suspended|instagram|facebook)\s+account\b', 'Account recovery solicitation'),
    (r'\b(?:crypto|bitcoin|forex)\s+(?:giveaway|signals?|investment)\b', 'High-risk financial promotion'),
    (r'\b(?:100%\s+free|limited\s+time\s+offer|act\s+now|no\s+risk)\b', 'High-pressure promotional language'),
    (r'\b(?:follow\s+me|check\s+my\s+page|link\s+in\s+my\s+bio)\b', 'Engagement or link bait'),
]
PROMO_PATTERNS = [
    (r'\bbuy\s+now\b', 'Buy-now promotion'),
    (r'\b(?:discount|promo\s+code|use\s+code)\b', 'Promotional discount'),
    (r'\b(?:subscribe\s+now|free\s+money)\b', 'Promotional phrase'),
]

def detect(text, duplicate=False):
    text = str(text or '')
    reasons = []
    score = 0
    urls = re.findall(r'https?://\S+|www\.\S+', text, re.I)
    mentions = re.findall(r'@\w+', text)
    lower = text.lower()

    for pattern, reason in SCAM_PATTERNS:
        if re.search(pattern, lower, re.I):
            reasons.append(reason); score += 2
    for pattern, reason in PROMO_PATTERNS:
        if re.search(pattern, lower, re.I):
            reasons.append(reason); score += 1
    if urls:
        score += 1
        reasons.append('Contains an external link')
    if len(urls) >= 2:
        score += 2; reasons.append('Multiple URLs in one comment')
    if re.search(r'(.)\1{5,}', text):
        score += 1; reasons.append('Excessive repeated characters')
    if duplicate:
        score += 2; reasons.append('Exact duplicate comment within this batch')
    if len(mentions) >= 5:
        score += 1; reasons.append('Unusually many mentions')
    if re.search(r'[!$₹]{3,}', text):
        score += 1; reasons.append('Excessive urgency or money symbols')

    # A single generic promotion/link is not enough by itself; scam language or
    # multiple independent indicators are required for the default flag.
    flagged = score >= 2
    return {
        'status': 'potential_spam' if flagged else 'normal',
        'score': min(score, 10),
        'confidence': round(min(0.55 + score * 0.045, 0.96), 2) if flagged else round(max(0.55, 0.92 - score * 0.08), 2),
        'reasons': reasons,
        'explanation': 'Heuristic risk estimate based on visible signals; review flagged comments and do not treat this as proof of malicious intent.'
    }
