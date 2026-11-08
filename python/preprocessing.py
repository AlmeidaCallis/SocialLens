import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords

# Install resources once with: python -m nltk.downloader punkt punkt_tab stopwords wordnet omw-1.4
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()
NEGATIONS = {"no", "not", "nor", "never", "n't"}

def preprocess(text):
    text = str(text or "")
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip()) if text.strip() else []
    try:
        words = word_tokenize(text)
    except LookupError:
        words = re.findall(r"#\w+|@\w+|[\w']+|[^\w\s]", text, re.UNICODE)
    lower = [w.lower() for w in words]
    cleaned = [re.sub(r"[^\w#@'\U0001F300-\U0001FAFF]", "", w) for w in lower]
    cleaned = [w for w in cleaned if w]
    try:
        stops = set(stopwords.words('english')) - NEGATIONS
    except LookupError:
        stops = {"the", "a", "an", "is", "are", "and", "to", "of", "in", "it", "this", "that", "for", "with"} - NEGATIONS
    filtered = [w for w in cleaned if w not in stops]
    words_for_lemma = [w for w in filtered if re.search(r"[a-zA-Z]", w)]
    try:
        lemmas = [lemmatizer.lemmatize(w) for w in words_for_lemma]
    except (LookupError, AttributeError):
        # Fallback keeps the experiment usable if the WordNet corpus loader fails.
        lemmas = [stemmer.stem(w) for w in words_for_lemma]
    return {"original": text, "sentences": sentences, "word_tokens": words, "lowercase_tokens": lower,
            "cleaned_tokens": cleaned, "cleaned_text": " ".join(cleaned), "stop_words_removed": filtered,
            "stop_word_text": " ".join(filtered), "stems": [stemmer.stem(w) for w in filtered],
            "lemmas": lemmas, "notes": "Negation words are preserved. Emoji handling is intentionally conservative; preprocessing should be adapted to the task."}
