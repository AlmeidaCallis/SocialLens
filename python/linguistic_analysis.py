import re
try:
 import spacy
 _nlp=spacy.load('en_core_web_sm')
except Exception:
 _nlp=None

def analyze(text, comparison=""):
 text=str(text or '')
 if _nlp:
  doc=_nlp(text); tokens=[{"token":t.text,"pos":t.pos_ or "X","tag":t.tag_,"lemma":t.lemma_} for t in doc]
  entities=[{"text":e.text,"label":e.label_,"start":e.start_char,"end":e.end_char} for e in doc.ents]
  comp_doc=_nlp(str(comparison or '')); comp_entities=[{"text":e.text,"label":e.label_} for e in comp_doc.ents]
  return {"tokens":tokens,"entities":entities,"comparison_entities":comp_entities,"engine":"spaCy en_core_web_sm"}
 # Honest fallback: NLTK POS if resources exist, regex tokens and no fabricated NER.
 try:
  import nltk
  words=nltk.word_tokenize(text); tagged=nltk.pos_tag(words)
  tokens=[{"token":w,"pos":tag,"tag":tag,"lemma":w.lower()} for w,tag in tagged]
 except Exception:
  tokens=[{"token":w,"pos":"UNAVAILABLE","tag":"UNAVAILABLE","lemma":w.lower()} for w in re.findall(r"\w+|[^\w\s]",text)]
 return {"tokens":tokens,"entities":[],"comparison_entities":[],"engine":"NLTK fallback; named entities unavailable without spaCy model","warning":"Install en_core_web_sm for POS and NER quality. No entities are fabricated."}
