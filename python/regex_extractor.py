import re
PATTERNS = {
 "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
 "url": r"https?://[^\s<>]+|\bwww\.[^\s<>]+",
 "phone": r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\d[ .-]?){8,12}\d(?!\w)",
 "date": r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
 "money": r"(?:₹|\$|€|\bINR\s?)\s?\d+(?:,\d{3})*(?:\.\d{1,2})?",
 "number": r"\b\d+(?:\.\d+)?%?\b",
 "hashtag": r"(?<!\w)#\w+", "mention": r"(?<!\w)@\w+", "repeated_characters": r"(.)\1{3,}"
}
def extract(text):
 text=str(text or ""); matches=[]
 for category,pattern in PATTERNS.items():
  for m in re.finditer(pattern,text,re.I): matches.append({"category":category,"text":m.group(0),"pattern":pattern,"start":m.start(),"end":m.end()})
 return {"original":text,"matches":matches,"cleaned_text":re.sub(r"[^\w\s#@.,!?$€₹%:/-]","",text),"prefix_checks":{"starts_with_http":text.strip().lower().startswith("http"),"starts_with_hash":text.strip().startswith("#"),"ends_with_question_mark":text.strip().endswith("?")},"warning":"Phone/date patterns are configurable heuristics; matches can be false positives and do not establish spam."}
